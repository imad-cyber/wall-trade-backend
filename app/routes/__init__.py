"""
Routes initialization and router collection.
Central point for registering all API routes.
"""
from fastapi import APIRouter

# Create router instance
api_router = APIRouter(prefix="/api/v1")

# Import and include route modules when they're created
# Example:
# from app.routes.company import router as company_router
# api_router.include_router(company_router, tags=["companies"])


def setup_routes(app):
    """
    Setup all routes in the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(api_router)
