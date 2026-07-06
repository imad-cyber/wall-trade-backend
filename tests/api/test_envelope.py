"""API envelope structure tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.dependencies import get_company_service, get_macro_service
from app.api.v1.schemas.company import CompanyOverviewResponse, ScorecardSchema, StockRangesSchema, PriceRangeSchema
from app.auth.dependencies import get_current_supabase_user, get_optional_user
from app.main import create_app
from app.services.company_service import CompanyService
from app.services.macro_service import MacroService


@pytest.fixture
def client():
    def override_user():
        return {"user_id": "test", "role": "authenticated"}

    def override_optional():
        return None

    def override_macro():
        service = MagicMock(spec=MacroService)
        service.get_latest.return_value = None
        return service

    app = create_app()
    app.dependency_overrides[get_current_supabase_user] = override_user
    app.dependency_overrides[get_optional_user] = override_optional
    app.dependency_overrides[get_macro_service] = override_macro
    return TestClient(app)


def test_response_has_contract_envelope(client):
    response = client.get("/api/v1/macro")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "timestamp" in data
    assert "request_id" in data
    assert "meta" in data


def test_response_has_request_id(client):
    response = client.get("/api/v1/macro")
    data = response.json()
    assert data["request_id"]


def test_health_contract_envelope(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ok"
    assert "request_id" in data


def test_company_overview_public_route(client):
    overview = CompanyOverviewResponse(
        ticker="OGDC",
        name="OGDC",
        exchange="PSX",
        currency="PKR",
        price=100.0,
        change=1.0,
        change_percent=1.0,
        status="Closed",
        last_updated="2026-06-23T15:30:00Z",
        ranges=StockRangesSchema(
            day_range=PriceRangeSchema(low=90, high=110, current=100),
            week_52=PriceRangeSchema(low=80, high=120, current=100),
        ),
        scorecard=ScorecardSchema(),
    )

    service = MagicMock(spec=CompanyService)
    service.get_overview = AsyncMock(return_value=(overview, False, 0))

    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    app.dependency_overrides[get_company_service] = lambda: service
    test_client = TestClient(app)

    response = test_client.get("/api/v1/companies/OGDC/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["ticker"] == "OGDC"
    assert body["request_id"]


def test_invalid_ticker_returns_400(client):
    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    test_client = TestClient(app)
    response = test_client.get("/api/v1/companies/INVALID!!/overview")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "TICKER_INVALID"
