"""Shared pytest fixtures."""
import asyncio
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def mock_db():
    db = MagicMock()
    table_mock = MagicMock()
    db.table.return_value = table_mock
    return db
