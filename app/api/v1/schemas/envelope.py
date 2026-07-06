"""API response envelope schemas — contract-compliant (API_SPECIFICATION.md §15)."""
from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.observability.context import get_ctx

T = TypeVar("T")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ApiMeta(BaseModel):
    provider: Optional[str] = None
    cached: bool = False
    cache_age_seconds: Optional[int] = None
    latency_ms: Optional[float] = None
    snapshot_date: Optional[str] = None
    version: Optional[str] = None


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class APIResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[ApiMeta] = None
    pagination: Optional[PaginationMeta] = None
    timestamp: str
    request_id: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiErrorResponse(BaseModel):
    error: ErrorBody
    timestamp: str
    request_id: str
    path: str


# Legacy aliases kept for gradual migration in imports
Meta = ApiMeta
ErrorDetail = ErrorBody


def make_response(
    data: T,
    *,
    cache_hit: bool = False,
    provider: Optional[str] = None,
    cache_age_seconds: Optional[int] = None,
    pagination: Optional[PaginationMeta] = None,
    start_time: Optional[float] = None,
) -> APIResponse[T]:
    """Build a contract-compliant success envelope."""
    import time

    ctx = get_ctx()
    latency = ctx.latency_ms
    if start_time is not None:
        latency = (time.perf_counter() - start_time) * 1000

    meta = ApiMeta(
        provider=provider,
        cached=cache_hit or ctx.cache_hit,
        cache_age_seconds=cache_age_seconds,
        latency_ms=latency,
    )

    return APIResponse(
        data=data,
        meta=meta,
        pagination=pagination,
        timestamp=_utc_now_iso(),
        request_id=ctx.request_id,
    )


def make_error_response(
    code: str,
    message: str,
    *,
    path: str = "",
    details: Optional[Any] = None,
) -> ApiErrorResponse:
    ctx = get_ctx()
    return ApiErrorResponse(
        error=ErrorBody(code=code, message=message, details=details),
        timestamp=_utc_now_iso(),
        request_id=ctx.request_id,
        path=path,
    )
