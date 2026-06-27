"""Provider tests with mocked HTTP."""
import httpx
import pytest

from app.core.http import AsyncHTTPClient
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.mapper import CompanyMapper
from app.providers.psx_proxy.client import PSXProxyClient


@pytest.mark.asyncio
async def test_capital_stake_get_company_profile():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"name": "Engro Corp", "pe": 10})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://api.test", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://api.test")
    client = CapitalStakeClient(http=http)
    profile = await client.get_company_profile("ENGRO")
    assert profile.ticker == "ENGRO"
    assert profile.name == "Engro Corp"
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


def test_company_mapper():
    profile = CompanyMapper.to_domain("ENGRO", {"companyName": "Engro"})
    assert profile.name == "Engro"
