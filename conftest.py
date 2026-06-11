"""
pytest configuration and fixtures.
"""
import pytest
import asyncio
from app.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create FastAPI application for testing."""
    return create_app()


@pytest.fixture
def settings():
    """Get application settings."""
    return get_settings()


@pytest.fixture
def mock_db():
    """Mock database client."""
    # TODO: Implement mock database
    pass
