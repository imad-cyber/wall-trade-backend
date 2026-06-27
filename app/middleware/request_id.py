"""Request ID middleware — propagates X-Request-ID through the stack."""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.context import RequestContext, set_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_ctx(
            RequestContext(
                request_id=request_id,
                path=request.url.path,
                method=request.method,
            )
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
