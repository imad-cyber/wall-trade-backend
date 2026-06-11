"""
Application factory and FastAPI configuration.
Creates and configures the FastAPI application instance.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.core import setup_logging, get_logger
from app.core.exceptions import AppException
from app.database import get_db_manager
from app.api import api_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    settings = get_settings()

    # Setup logging
    setup_logging(level=settings.LOG_LEVEL, format_type=settings.LOG_FORMAT)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Manage application startup and shutdown events.
        """
        # Startup
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        
        try:
            db_manager = get_db_manager()
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

        yield

        # Shutdown
        logger.info("Shutting down application")
        db_manager.close()

    # Create FastAPI instance
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        """Handle custom application exceptions."""
        logger.error(f"Application error: {exc.error_code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    @app.get("/health", tags=["health"])
    async def root_health_check():
        """Root-level health check for infrastructure probes."""
        return {
            "status": "healthy",
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Include versioned API routes
    app.include_router(api_router)

    return app


if __name__ == "__main__":
    app = create_app()
    settings = get_settings()
    
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
