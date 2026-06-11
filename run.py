"""
Run script for local development.
This script sets up and runs the FastAPI application.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import create_app
from app.config import get_settings
import uvicorn


def main():
    """Main entry point for the application."""
    settings = get_settings()

    # Create application
    app = create_app()

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Run the application
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        factory = True
    )


if __name__ == "__main__":
    main()
