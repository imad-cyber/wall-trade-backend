"""
Wall-Trade-Backend application package.
Main entry point for the FastAPI application.
"""
from app.main import create_app

__version__ = "1.0.0"
__title__ = "Wall-Trade-Backend"

# Create the FastAPI application instance
app = create_app()
