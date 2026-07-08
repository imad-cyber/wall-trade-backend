"""News service — N1, N2."""
import logging
from typing import Any, Optional

from app.api.v1.schemas.news import NewsResponse
from app.core.exceptions import ExternalServiceError
from app.core.memory_cache import get_memory_cache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import _rows_from_list, map_news
from app.utils.tiering import get_user_tier

logger = logging.getLogger(__name__)

CACHE_TTL = 300
MAX_SECTOR_NEWS_ATTEMPTS = 3

# PSX symbols used when sector-wide news returns no articles.
MARKET_NEWS_FALLBACK_TICKERS: tuple[str, ...] = (
    "OGDC",
    "ENGRO",
    "MEBL",
    "HBL",
    "LUCK",
    "SYS",
    "PPL",
    "UBL",
    "BAFL",
    "TRG",
)


class NewsService:
    def __init__(self, capital_stake: CapitalStakeClient):
        self.capital_stake = capital_stake
        self._cache = get_memory_cache()

    def _log_news_raw(self, context: str, raw: Any, articles: list[dict[str, Any]]) -> None:
        logger.debug(
            "CS news raw response context=%s keys=%s articles_count=%d",
            context,
            list(raw.keys()) if isinstance(raw, dict) else type(raw).__name__,
            len(articles),
        )

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
        self._log_news_raw(f"ticker:{ticker.upper()}", raw, articles)
        result = map_news(ticker, articles, category=category, page=page, page_size=page_size, tier=tier)
        self._cache.set(cache_key, result, CACHE_TTL)
        return result, False, 0

    async def _aggregate_company_news(self, tickers: tuple[str, ...]) -> list[dict[str, Any]]:
        articles: list[dict[str, Any]] = []
        seen: set[str] = set()
        for ticker in tickers:
            try:
                raw = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_company_news(ticker)
                )
                for row in _rows_from_list(raw):
                    headline = str(
                        row.get("headline") or row.get("title") or ""
                    ).strip()
                    if not headline:
                        continue
                    dedupe_key = headline.lower()
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    articles.append(row)
            except ExternalServiceError:
                continue
        return articles

    async def _fetch_sector_news(self, max_sectors: int = MAX_SECTOR_NEWS_ATTEMPTS) -> list[dict[str, Any]]:
        sector_codes = await self.capital_stake._all_sector_codes()
        articles: list[dict[str, Any]] = []
        seen: set[str] = set()
        for sector_code in sector_codes[:max_sectors]:
            try:
                raw = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_sector_news(sector_code)
                )
                batch = _rows_from_list(raw)
                self._log_news_raw(f"sector:{sector_code}", raw, batch)
                for row in batch:
                    headline = str(row.get("headline") or row.get("title") or "").strip()
                    dedupe_key = headline.lower() if headline else str(row.get("link", ""))
                    if dedupe_key and dedupe_key in seen:
                        continue
                    if dedupe_key:
                        seen.add(dedupe_key)
                    articles.append(row)
                if articles:
                    break
            except ExternalServiceError:
                continue
        return articles

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

        articles = await self._fetch_sector_news()
        if not articles:
            articles = await self._aggregate_company_news(MARKET_NEWS_FALLBACK_TICKERS)
        result = map_news("MARKET", articles, category="Recent", page=page, page_size=page_size, tier=tier)
        self._cache.set(cache_key, result, CACHE_TTL)
        return result, False, 0
