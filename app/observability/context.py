"""Request-scoped context propagation via contextvars."""
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RequestContext:
    """Per-request observability context."""

    request_id: str = ""
    latency_ms: float = 0.0
    cache_hit: bool = False
    path: str = ""
    method: str = ""
    provider_latencies: dict[str, float] = field(default_factory=dict)
    ai_latency_ms: Optional[float] = None


_ctx: ContextVar[Optional[RequestContext]] = ContextVar("request_context", default=None)


def get_ctx() -> RequestContext:
    ctx = _ctx.get()
    if ctx is None:
        ctx = RequestContext()
        _ctx.set(ctx)
    return ctx


def set_ctx(ctx: RequestContext) -> None:
    _ctx.set(ctx)


def reset_ctx() -> None:
    _ctx.set(None)
