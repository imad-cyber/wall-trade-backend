"""Provider tests with mocked HTTP."""
import httpx
import pytest

from app.core.http import AsyncHTTPClient
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.mapper import CompanyMapper, map_quote_to_stock_data
from app.providers.psx_proxy.client import PSXProxyClient


@pytest.mark.asyncio
async def test_capital_stake_get_single_quote():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/quotes/ENGRO")
        return httpx.Response(200, json={"lastPrice": 282.5, "name": "Engro Corp"})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com")
    client = CapitalStakeClient(http=http)
    quote = await client.get_single_quote("ENGRO")
    assert quote["lastPrice"] == 282.5
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_get_stock_quote():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"lastPrice": 100, "change": 2, "changePercent": 2.0})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com")
    client = CapitalStakeClient(http=http)
    stock = await client.get_stock_quote("HBL")
    assert stock.ticker == "HBL"
    assert stock.price == 100.0
    await http.aclose()


@pytest.mark.asyncio
async def test_psx_proxy_get_all_prices():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"prices": [{"ticker": "HBL", "price": 100}]})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://psx.test", provider_name="psx_proxy")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://psx.test")
    client = PSXProxyClient(http=http)
    prices = await client.get_all_prices()
    assert len(prices) == 1
    assert prices[0].ticker == "HBL"
    await http.aclose()


def test_company_mapper_legacy():
    profile = CompanyMapper.to_domain("ENGRO", {"companyName": "Engro"})
    assert profile.name == "Engro"


def test_map_quote_to_stock_data():
    stock = map_quote_to_stock_data("OGDC", {"lastPrice": 145.82, "change": -3.21, "changePercent": -2.15})
    assert stock.ticker == "OGDC"
    assert stock.price == 145.82
