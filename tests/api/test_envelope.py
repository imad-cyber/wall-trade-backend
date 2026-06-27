"""API envelope structure tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.api.v1.dependencies import get_macro_service
from app.auth.dependencies import get_current_supabase_user
from app.main import create_app
from app.services.macro_service import MacroService


@pytest.fixture
def client():
    def override_user():
        return {"user_id": "test", "role": "authenticated"}

    def override_macro():
        service = MagicMock(spec=MacroService)
        service.get_latest.return_value = None
        return service

    app = create_app()
    app.dependency_overrides[get_current_supabase_user] = override_user
    app.dependency_overrides[get_macro_service] = override_macro
    return TestClient(app)


def test_response_has_meta_field(client):
    response = client.get("/api/v1/macro")
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert data["success"] is True
    assert isinstance(data["errors"], list)


def test_response_has_request_id(client):
    response = client.get("/api/v1/macro")
    data = response.json()
    assert data["meta"]["request_id"]


def test_error_response_has_errors_list(client):
    response = client.get("/api/v1/company/TEST")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "errors" in detail or "missing_configuration" in detail
