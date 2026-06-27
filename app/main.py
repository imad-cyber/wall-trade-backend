"""
Application factory and FastAPI configuration.
"""
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.api import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.lifespan import lifespan
from app.core.logging import get_logger, setup_logging
from app.core.middleware import register_middleware
from app.api.v1.schemas.envelope import ErrorDetail, APIResponse, Meta, make_error_response
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
    async def app_exception_handler(request, exc: AppException):
        logger.error("Application error: %s - %s", exc.error_code, exc.message)
        body = make_error_response(exc.error_code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        logger.warning("Validation error: %s", exc.errors())
        body = APIResponse(
            success=False,
            data=None,
            meta=Meta(),
            errors=[
                ErrorDetail(code="VALIDATION_ERROR", message="Request validation failed"),
            ],
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error("Unexpected error: %s", exc, exc_info=True)
        body = make_error_response("INTERNAL_SERVER_ERROR", "An unexpected error occurred")
        return JSONResponse(status_code=500, content=body.model_dump())

    @app.get("/health", tags=["health"])
    async def root_health_check():
        return {
            "status": "healthy",
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

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
