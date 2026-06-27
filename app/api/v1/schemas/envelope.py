"""API response envelope schemas."""
import time
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.observability.context import get_ctx

T = TypeVar("T")


class Meta(BaseModel):
    request_id: str = ""
    latency_ms: float = 0.0
    cache_hit: bool = False


class ErrorDetail(BaseModel):
    code: str
    message: str


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: Meta = Field(default_factory=Meta)
    errors: list[ErrorDetail] = Field(default_factory=list)


def make_response(
    data: T,
    *,
    cache_hit: bool = False,
    start_time: Optional[float] = None,
) -> APIResponse[T]:
    """Build a standard APIResponse using RequestContext for meta fields."""
    ctx = get_ctx()
    latency = ctx.latency_ms
    if start_time is not None:
        latency = (time.perf_counter() - start_time) * 1000
    return APIResponse(
        success=True,
        data=data,
        meta=Meta(
            request_id=ctx.request_id,
            latency_ms=latency,
            cache_hit=cache_hit or ctx.cache_hit,
        ),
        errors=[],
    )


def make_error_response(
    code: str,
    message: str,
    *,
    status_data: None = None,
) -> APIResponse[None]:
    ctx = get_ctx()
    return APIResponse(
        success=False,
        data=status_data,
        meta=Meta(request_id=ctx.request_id, latency_ms=ctx.latency_ms),
        errors=[ErrorDetail(code=code, message=message)],
    )
