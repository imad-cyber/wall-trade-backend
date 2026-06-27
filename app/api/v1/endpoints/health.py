"""
API v1 endpoints - health check and status endpoints.
"""
from fastapi import APIRouter, status
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status and application info
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
