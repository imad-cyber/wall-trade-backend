"""
Application factory and FastAPI configuration.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.lifespan import lifespan
from app.core.logging import get_logger, setup_logging
from app.core.middleware import register_middleware
from app.api.v1.schemas.envelope import make_error_response
from app.observability.metrics import metrics_response

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, format_type=settings.LOG_FORMAT)

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    register_middleware(app, settings)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error("Application error: %s - %s", exc.error_code, exc.message)
        body = make_error_response(
            exc.error_code,
            exc.message,
            path=str(request.url.path),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Validation error: %s", exc.errors())
        body = make_error_response(
            "VALIDATION_ERROR",
            "Request validation failed",
            path=str(request.url.path),
            details=exc.errors(),
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(status_code=exc.status_code, content=detail)

        code = "INTERNAL_ERROR"
        message = str(detail)
        if exc.status_code == 401:
            code = "TOKEN_INVALID"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 503:
            code = "SERVICE_UNAVAILABLE"

        body = make_error_response(code, message, path=str(request.url.path))
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error("Unexpected error: %s", exc, exc_info=True)
        body = make_error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred",
            path=str(request.url.path),
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    @app.get("/health", tags=["health"])
    async def root_health_check():
        from app.api.v1.schemas.envelope import make_response

        return make_response(
            {
                "status": "ok",
                "application": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        ).model_dump()

    @app.get("/metrics", tags=["observability"], include_in_schema=False)
    async def prometheus_metrics():
        content, content_type = metrics_response()
        return Response(content=content, media_type=content_type)

    app.include_router(api_router)
    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    cfg = get_settings()
    uvicorn.run(app, host=cfg.HOST, port=cfg.PORT, reload=cfg.RELOAD)
