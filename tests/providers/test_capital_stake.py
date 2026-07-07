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
        assert request.url.path.endswith("/market/stock")
        assert request.url.params.get("symbol") == "ENGRO"
        return httpx.Response(200, json={"status": "ok", "data": {"ldcp": 282.5, "name": "Engro Corp"}})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    quote = await client.get_single_quote("ENGRO")
    assert quote["data"]["ldcp"] == 282.5
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_get_stock_quote():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "data": {"c": 100, "ch": 2, "pch": 2.0}})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    stock = await client.get_stock_quote("HBL")
    assert stock.ticker == "HBL"
    assert stock.price == 100.0
    await http.aclose()


@pytest.mark.asyncio
async def test_get_all_tickers_uses_fallback_when_collection_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"status": "error", "message": "not found"})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)

    tickers = await client.get_all_tickers()
    rows = client._unwrap_data(tickers)
    assert len(rows) > 0
    assert any(str(row.get("ticker", "")).upper() == "OGDC" for row in rows)
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_stock_404_raises_ticker_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"status": "error"})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)

    from app.core.exceptions import ResourceNotFoundError

    with pytest.raises(ResourceNotFoundError) as exc_info:
        await client.get_single_quote("FAKE")
    assert "Ticker FAKE" in str(exc_info.value)
    await http.aclose()


@pytest.mark.asyncio
async def test_company_overview_survives_tickers_404():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/market/stock"):
            return httpx.Response(
                200,
                json={"status": "ok", "data": {"s": "OGDC", "c": 250.5, "ch": 1.2, "pch": 0.5}},
            )
        if request.url.path.endswith("/market/tickers"):
            return httpx.Response(404, json={"status": "error"})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    overview = await client.get_company_overview("OGDC")
    assert overview.ticker == "OGDC"
    assert overview.price == 250.5
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_get_single_quote_list_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "data": [
                    {
                        "symbol": "OGDC",
                        "name": "Oil & Gas Development Company Limited",
                        "ldcp": 348.72,
                        "ucap": 383.59,
                        "lcap": 313.85,
                        "high52": 352,
                        "low52": 220.99,
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    stock = await client.get_stock_quote("OGDC")
    assert stock.ticker == "OGDC"
    assert stock.price == 348.72
    assert stock.ranges.day_range.high == 383.59
    assert stock.ranges.week_52.low == 220.99
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_get_indices_falls_back_to_index_quotes():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/market/tickers"):
            return httpx.Response(404, json={"status": "error"})
        if request.url.path.endswith("/market/stock"):
            symbol = request.url.params.get("symbol")
            if symbol == "KSE100":
                return httpx.Response(
                    200,
                    json={"status": "ok", "data": [{"symbol": "KSE100", "ldcp": 82000, "pch": 0.12}]},
                )
            return httpx.Response(404, json={"status": "error"})
        return httpx.Response(404, json={"status": "error"})

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    indices = await client.get_indices()
    rows = client._unwrap_data(indices)
    assert len(rows) >= 1
    assert rows[0]["symbol"] == "KSE100"
    await http.aclose()


@pytest.mark.asyncio
async def test_capital_stake_get_indices_filters_idx_rows():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/market/indices"):
            return httpx.Response(404, json={"status": "error"})
        assert request.url.path.endswith("/market/tickers")
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "data": [
                    {"m": "REG", "s": "HBL", "c": 100, "ch": 1, "pch": 1.0},
                    {"m": "IDX", "s": "KSE100", "c": 82000, "ch": 100, "pch": 0.12},
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    http = AsyncHTTPClient("https://uat.csapis.com/3.0", provider_name="capital_stake")
    http._client = httpx.AsyncClient(transport=transport, base_url="https://uat.csapis.com/3.0")
    client = CapitalStakeClient(http=http)
    indices = await client.get_indices()
    rows = client._unwrap_data(indices)
    assert len(rows) == 1
    assert rows[0]["s"] == "KSE100"
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


def test_map_quote_to_stock_data_ldcp():
    stock = map_quote_to_stock_data(
        "OGDC",
        {
            "symbol": "OGDC",
            "name": "Oil & Gas Development Company Limited",
            "ldcp": 348.72,
            "ucap": 383.59,
            "lcap": 313.85,
            "high52": 352,
            "low52": 220.99,
        },
    )
    assert stock.ticker == "OGDC"
    assert stock.price == 348.72
    assert stock.ranges.day_range.high == 383.59
    assert stock.ranges.week_52.low == 220.99


def test_map_quote_to_stock_data():
    stock = map_quote_to_stock_data("OGDC", {"lastPrice": 145.82, "change": -3.21, "changePercent": -2.15})
    assert stock.ticker == "OGDC"
    assert stock.price == 145.82
