"""Contract endpoint smoke tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.dependencies import (
    get_company_service,
    get_market_service,
    get_users_service,
)
from app.api.v1.schemas.company import (
    CompanyOverviewResponse,
    PriceRangeSchema,
    ScorecardSchema,
    StockRangesSchema,
)
from app.api.v1.schemas.market import OHLCVResponse
from app.api.v1.schemas.users import UserProfileResponse
from app.auth.dependencies import get_current_supabase_user, get_optional_user
from app.main import create_app
from app.services.company_service import CompanyService
from app.services.market_service import MarketService
from app.services.users_service import UsersService


@pytest.fixture
def contract_client():
    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    app.dependency_overrides[get_current_supabase_user] = lambda: {
        "user_id": "test-user",
        "email": "test@example.com",
    }
    return TestClient(app)


def test_market_quote_route(contract_client):
    quote = MagicMock()
    quote.model_dump.return_value = {"ticker": "OGDC", "price": 100.0}
    service = MagicMock(spec=MarketService)
    service.get_quote = AsyncMock(return_value=(quote, False, 0))

    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    app.dependency_overrides[get_market_service] = lambda: service
    client = TestClient(app)

    response = client.get("/api/v1/market/quote/OGDC")
    assert response.status_code == 200
    assert response.json()["data"]["ticker"] == "OGDC"


def test_market_ohlcv_route(contract_client):
    ohlcv = OHLCVResponse(ticker="OGDC", range="2y", interval="1d", points=[])
    service = MagicMock(spec=MarketService)
    service.get_ohlcv = AsyncMock(return_value=(ohlcv, False, 0))

    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    app.dependency_overrides[get_market_service] = lambda: service
    client = TestClient(app)

    response = client.get("/api/v1/market/OGDC/ohlcv?range=2y&interval=1d")
    assert response.status_code == 200
    assert response.json()["data"]["ticker"] == "OGDC"


def test_users_me_route():
    profile = UserProfileResponse(
        id="test-user",
        email="test@example.com",
        subscription_tier="free",
    )
    service = MagicMock(spec=UsersService)
    service.get_profile.return_value = profile

    app = create_app()
    app.dependency_overrides[get_current_supabase_user] = lambda: {
        "user_id": "test-user",
        "email": "test@example.com",
    }
    app.dependency_overrides[get_users_service] = lambda: service
    client = TestClient(app)

    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"


def test_companies_statistics_route():
    from app.api.v1.schemas.company import CompanyStatisticsResponse

    stats = CompanyStatisticsResponse(ticker="OGDC", columns=[])
    service = MagicMock(spec=CompanyService)
    service.get_statistics = AsyncMock(return_value=(stats, False, 0))

    app = create_app()
    app.dependency_overrides[get_optional_user] = lambda: None
    app.dependency_overrides[get_company_service] = lambda: service
    client = TestClient(app)

    response = client.get("/api/v1/companies/OGDC/statistics")
    assert response.status_code == 200
    assert response.json()["data"]["ticker"] == "OGDC"
