"""Crypto market data service — CoinGecko proxy with caching."""
from typing import Any, Optional

from app.core.exceptions import ExternalServiceError
from app.core.memory_cache import get_memory_cache
from app.providers.coingecko.client import CoinGeckoClient

PRICE_CACHE_TTL = 60
MARKETS_CACHE_TTL = 60
DETAIL_CACHE_TTL = 300
CHART_CACHE_TTL = 3600
TRENDING_CACHE_TTL = 300
SEARCH_CACHE_TTL = 300
ONCHAIN_CACHE_TTL = 120


class CryptoService:
    def __init__(self, client: CoinGeckoClient | None = None):
        self.client = client or CoinGeckoClient()
        self._cache = get_memory_cache()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    def missing_config(self) -> list[str]:
        if self.is_configured():
            return []
        return ["COINGECKO_API_KEY"]

    def _ensure_configured(self) -> None:
        if not self.is_configured():
            raise ExternalServiceError(
                "CoinGecko",
                "API key not configured",
                error_code="SERVICE_UNAVAILABLE",
            )

    async def _cached(self, key: str, ttl: int, factory):
        cached = self._cache.get(key)
        if cached is not None:
            return cached[0], True, cached[1]
        self._ensure_configured()
        result = await factory()
        self._cache.set(key, result, ttl)
        return result, False, 0

    async def ping(self) -> tuple[dict[str, Any], bool, int]:
        return await self._cached("crypto:ping", 30, self.client.ping)

    async def get_api_key_usage(self) -> tuple[dict[str, Any], bool, int]:
        return await self._cached("crypto:key", 60, self.client.get_api_key_usage)

    async def get_simple_price(self, **kwargs) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:price:{kwargs}"
        return await self._cached(
            cache_key,
            PRICE_CACHE_TTL,
            lambda: self.client.get_simple_price(**kwargs),
        )

    async def get_coins_markets(self, **kwargs) -> tuple[list[dict[str, Any]], bool, int]:
        cache_key = f"crypto:markets:{kwargs}"
        return await self._cached(
            cache_key,
            MARKETS_CACHE_TTL,
            lambda: self.client.get_coins_markets(**kwargs),
        )

    async def get_coin_detail(self, coin_id: str, **kwargs) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:coin:{coin_id}:{kwargs}"
        return await self._cached(
            cache_key,
            DETAIL_CACHE_TTL,
            lambda: self.client.get_coin_detail(coin_id, **kwargs),
        )

    async def get_market_chart(self, coin_id: str, **kwargs) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:chart:{coin_id}:{kwargs}"
        return await self._cached(
            cache_key,
            CHART_CACHE_TTL,
            lambda: self.client.get_market_chart(coin_id, **kwargs),
        )

    async def get_market_chart_range(
        self,
        coin_id: str,
        **kwargs,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:chart_range:{coin_id}:{kwargs}"
        return await self._cached(
            cache_key,
            CHART_CACHE_TTL,
            lambda: self.client.get_market_chart_range(coin_id, **kwargs),
        )

    async def get_ohlc(self, coin_id: str, **kwargs) -> tuple[list[list[float]], bool, int]:
        cache_key = f"crypto:ohlc:{coin_id}:{kwargs}"
        return await self._cached(
            cache_key,
            CHART_CACHE_TTL,
            lambda: self.client.get_ohlc(coin_id, **kwargs),
        )

    async def get_trending(self) -> tuple[dict[str, Any], bool, int]:
        return await self._cached("crypto:trending", TRENDING_CACHE_TTL, self.client.get_trending)

    async def get_top_gainers_losers(self, **kwargs) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:gainers_losers:{kwargs}"
        return await self._cached(
            cache_key,
            TRENDING_CACHE_TTL,
            lambda: self.client.get_top_gainers_losers(**kwargs),
        )

    async def search(self, query: str) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:search:{query.lower()}"
        return await self._cached(
            cache_key,
            SEARCH_CACHE_TTL,
            lambda: self.client.search(query),
        )

    async def get_onchain_token_price(
        self,
        network: str,
        address: str,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:price:{network}:{address.lower()}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_token_price(network, address),
        )

    async def get_onchain_pool(
        self,
        network: str,
        address: str,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:pool:{network}:{address.lower()}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_pool(network, address),
        )

    async def get_onchain_trending_pools(
        self,
        network: Optional[str] = None,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:trending:{network or 'all'}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_trending_pools(network),
        )

    async def get_onchain_new_pools(
        self,
        network: Optional[str] = None,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:new:{network or 'all'}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_new_pools(network),
        )

    async def get_onchain_megafilter(self, **kwargs) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:megafilter:{kwargs}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_megafilter(**kwargs),
        )

    async def get_onchain_token_info(
        self,
        network: str,
        address: str,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:info:{network}:{address.lower()}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_token_info(network, address),
        )

    async def get_onchain_token_top_holders(
        self,
        network: str,
        address: str,
    ) -> tuple[dict[str, Any], bool, int]:
        cache_key = f"crypto:onchain:holders:{network}:{address.lower()}"
        return await self._cached(
            cache_key,
            ONCHAIN_CACHE_TTL,
            lambda: self.client.get_onchain_token_top_holders(network, address),
        )
