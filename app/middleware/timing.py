"""Timing middleware — adds X-Process-Time header and records latency."""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.context import get_ctx
from app.observability.metrics import record_request_latency, record_request_total


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

        ctx = get_ctx()
        ctx.latency_ms = elapsed_ms
        record_request_latency(request.url.path, elapsed_ms)
        record_request_total(request.url.path, request.method, response.status_code)
        return response
