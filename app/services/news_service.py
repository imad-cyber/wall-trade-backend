"""News service — N1, N2."""
from typing import Any, Optional

from app.api.v1.schemas.news import NewsResponse
from app.core.exceptions import ExternalServiceError
from app.core.memory_cache import get_memory_cache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import _rows_from_list, map_news
from app.utils.tiering import get_user_tier

CACHE_TTL = 300


class NewsService:
    def __init__(self, capital_stake: CapitalStakeClient):
        self.capital_stake = capital_stake
        self._cache = get_memory_cache()

    async def get_ticker_news(
        self,
        ticker: str,
        category: str = "Recent",
        page: int = 1,
        page_size: int = 20,
        user: Optional[dict[str, Any]] = None,
    ) -> tuple[NewsResponse, bool, int]:
        tier = get_user_tier(user)
        cache_key = f"news:{ticker.upper()}:{category}:{page}:{page_size}:{tier}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached[0], True, cached[1]

        if not self.capital_stake.is_configured():
            raise ExternalServiceError(
                "Capital Stake", "API token not configured", error_code="SERVICE_UNAVAILABLE",
            )

        raw = self.capital_stake._unwrap_data(await self.capital_stake.get_company_news(ticker))
        articles = _rows_from_list(raw)
        result = map_news(ticker, articles, category=category, page=page, page_size=page_size, tier=tier)
        self._cache.set(cache_key, result, CACHE_TTL)
        return result, False, 0

    async def get_market_news(
        self,
        page: int = 1,
        page_size: int = 20,
        user: Optional[dict[str, Any]] = None,
    ) -> tuple[NewsResponse, bool, int]:
        tier = get_user_tier(user)
        cache_key = f"news:market:{page}:{page_size}:{tier}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached[0], True, cached[1]

        if not self.capital_stake.is_configured():
            raise ExternalServiceError(
                "Capital Stake", "API token not configured", error_code="SERVICE_UNAVAILABLE",
            )

        raw = self.capital_stake._unwrap_data(await self.capital_stake.get_sector_news("all"))
        articles = _rows_from_list(raw)
        result = map_news("MARKET", articles, category="Recent", page=page, page_size=page_size, tier=tier)
        self._cache.set(cache_key, result, CACHE_TTL)
        return result, False, 0
