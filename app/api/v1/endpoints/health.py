"""
API v1 endpoints - health check and status endpoints.
"""
from fastapi import APIRouter, status

from app.api.v1.schemas.envelope import make_response
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Contract-compliant health check at /api/v1/health."""
    settings = get_settings()
    return make_response(
        {
            "status": "ok",
            "application": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )
