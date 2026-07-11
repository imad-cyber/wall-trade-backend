"""CoinGecko API v3 and GeckoTerminal client."""
from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, RateLimitError, ResourceNotFoundError
from app.core.http import get_http_client


class CoinGeckoClient:
    """HTTP client for CoinGecko aggregated data and GeckoTerminal on-chain data."""

    def __init__(self, http=None):
        settings = get_settings()
        self._settings = settings
        self._http = http or get_http_client(
            "coingecko",
            settings.coingecko_base_url,
            api_key=settings.COINGECKO_API_KEY,
            api_key_header=settings.coingecko_api_key_header,
        )

    def is_configured(self) -> bool:
        return bool(self._settings.COINGECKO_API_KEY)

    async def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        try:
            return await self._http.get(path, params=params)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            detail = ""
            try:
                detail = exc.response.text[:300]
            except Exception:
                pass
            if status == 404:
                raise ResourceNotFoundError(path) from exc
            if status == 429:
                raise RateLimitError("CoinGecko rate limit exceeded") from exc
            if status == 401:
                raise ExternalServiceError(
                    "CoinGecko",
                    "Invalid API key or wrong plan/base URL",
                    error_code="AUTH_ERROR",
                ) from exc
            if status == 400 and "10011" in detail:
                raise ExternalServiceError(
                    "CoinGecko",
                    "Demo API key used with Pro URL — set COINGECKO_PLAN=demo",
                    error_code="AUTH_ERROR",
                ) from exc
            if status == 400 and "10010" in detail:
                raise ExternalServiceError(
                    "CoinGecko",
                    "Pro API key used with Demo URL — set COINGECKO_PLAN=pro",
                    error_code="AUTH_ERROR",
                ) from exc
            raise ExternalServiceError(
                "CoinGecko",
                f"HTTP {status}: {detail}",
                error_code="PROVIDER_ERROR",
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "CoinGecko",
                str(exc),
                error_code="SERVICE_UNAVAILABLE",
            ) from exc

    async def ping(self) -> dict[str, Any]:
        return await self._get("/ping")

    async def get_api_key_usage(self) -> dict[str, Any]:
        return await self._get("/key")

    async def get_simple_price(
        self,
        *,
        ids: Optional[str] = None,
        names: Optional[str] = None,
        symbols: Optional[str] = None,
        vs_currencies: str = "usd",
        include_market_cap: bool = False,
        include_24hr_vol: bool = False,
        include_24hr_change: bool = False,
        include_last_updated_at: bool = False,
        precision: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"vs_currencies": vs_currencies}
        if ids:
            params["ids"] = ids
        if names:
            params["names"] = names
        if symbols:
            params["symbols"] = symbols
        if include_market_cap:
            params["include_market_cap"] = "true"
        if include_24hr_vol:
            params["include_24hr_vol"] = "true"
        if include_24hr_change:
            params["include_24hr_change"] = "true"
        if include_last_updated_at:
            params["include_last_updated_at"] = "true"
        if precision is not None:
            params["precision"] = precision
        return await self._get("/simple/price", params)

    async def get_coins_markets(
        self,
        *,
        vs_currency: str = "usd",
        ids: Optional[str] = None,
        category: Optional[str] = None,
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        sparkline: bool = False,
        price_change_percentage: Optional[str] = None,
        locale: str = "en",
        precision: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": str(sparkline).lower(),
            "locale": locale,
        }
        if ids:
            params["ids"] = ids
        if category:
            params["category"] = category
        if price_change_percentage:
            params["price_change_percentage"] = price_change_percentage
        if precision is not None:
            params["precision"] = precision
        result = await self._get("/coins/markets", params)
        return result if isinstance(result, list) else []

    async def get_coin_detail(
        self,
        coin_id: str,
        *,
        localization: bool = False,
        tickers: bool = False,
        market_data: bool = True,
        community_data: bool = False,
        developer_data: bool = False,
        sparkline: bool = False,
    ) -> dict[str, Any]:
        params = {
            "localization": str(localization).lower(),
            "tickers": str(tickers).lower(),
            "market_data": str(market_data).lower(),
            "community_data": str(community_data).lower(),
            "developer_data": str(developer_data).lower(),
            "sparkline": str(sparkline).lower(),
        }
        return await self._get(f"/coins/{coin_id}", params)

    async def get_market_chart(
        self,
        coin_id: str,
        *,
        vs_currency: str = "usd",
        days: str = "30",
        interval: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"vs_currency": vs_currency, "days": days}
        if interval:
            params["interval"] = interval
        return await self._get(f"/coins/{coin_id}/market_chart", params)

    async def get_market_chart_range(
        self,
        coin_id: str,
        *,
        vs_currency: str = "usd",
        from_timestamp: int,
        to_timestamp: int,
    ) -> dict[str, Any]:
        params = {
            "vs_currency": vs_currency,
            "from": from_timestamp,
            "to": to_timestamp,
        }
        return await self._get(f"/coins/{coin_id}/market_chart/range", params)

    async def get_ohlc(
        self,
        coin_id: str,
        *,
        vs_currency: str = "usd",
        days: str = "30",
    ) -> list[list[float]]:
        params = {"vs_currency": vs_currency, "days": days}
        result = await self._get(f"/coins/{coin_id}/ohlc", params)
        return result if isinstance(result, list) else []

    async def get_trending(self) -> dict[str, Any]:
        return await self._get("/search/trending")

    async def get_top_gainers_losers(
        self,
        *,
        vs_currency: str = "usd",
        duration: str = "24h",
        price_change_percentage: Optional[str] = None,
        top_coins: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"vs_currency": vs_currency, "duration": duration}
        if price_change_percentage:
            params["price_change_percentage"] = price_change_percentage
        if top_coins:
            params["top_coins"] = top_coins
        return await self._get("/coins/top_gainers_losers", params)

    async def search(self, query: str) -> dict[str, Any]:
        return await self._get("/search", {"query": query})

    async def get_onchain_token_price(
        self,
        network: str,
        address: str,
    ) -> dict[str, Any]:
        return await self._get(
            f"/onchain/simple/networks/{network}/token_price/{address}",
        )

    async def get_onchain_pool(self, network: str, address: str) -> dict[str, Any]:
        return await self._get(f"/onchain/networks/{network}/pools/{address}")

    async def get_onchain_trending_pools(
        self,
        network: Optional[str] = None,
    ) -> dict[str, Any]:
        path = (
            f"/onchain/networks/{network}/trending_pools"
            if network
            else "/onchain/networks/trending_pools"
        )
        return await self._get(path)

    async def get_onchain_new_pools(
        self,
        network: Optional[str] = None,
    ) -> dict[str, Any]:
        path = (
            f"/onchain/networks/{network}/new_pools"
            if network
            else "/onchain/networks/new_pools"
        )
        return await self._get(path)

    async def get_onchain_megafilter(
        self,
        *,
        sort: str = "pool_created_at_desc",
        **filters: Any,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"sort": sort, **filters}
        return await self._get("/onchain/pools/megafilter", params)

    async def get_onchain_token_info(self, network: str, address: str) -> dict[str, Any]:
        return await self._get(f"/onchain/networks/{network}/tokens/{address}/info")

    async def get_onchain_token_top_holders(
        self,
        network: str,
        address: str,
    ) -> dict[str, Any]:
        return await self._get(
            f"/onchain/networks/{network}/tokens/{address}/top_holders",
        )
