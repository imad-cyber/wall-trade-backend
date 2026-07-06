"""Company profile service — C1 through C8."""
from typing import Any, Optional

from app.api.v1.schemas.company import (
    CompanyOverviewResponse,
    CompanyProfileResponse,
    CompanyStatisticsResponse,
    DividendResponse,
    EarningsResponse,
    FaqResponse,
    OwnershipResponse,
    PeriodReturnsResponse,
)
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.memory_cache import get_memory_cache
from app.domain.company.models import CompanyProfile
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import (
    compute_period_returns,
    map_dividends,
    map_earnings,
    map_faq,
    map_ohlcv,
    map_ownership,
    map_statistics,
    validate_ohlcv_params,
)
from app.utils.tiering import get_user_tier

OVERVIEW_CACHE_TTL = 300
PROFILE_CACHE_TTL = 86400
STATS_CACHE_TTL = 86400
EARNINGS_CACHE_TTL = 86400
DIVIDENDS_CACHE_TTL = 86400
OWNERSHIP_CACHE_TTL = 86400
PERIOD_RETURNS_CACHE_TTL = 3600
FAQ_CACHE_TTL = 3600


class CompanyService:
    def __init__(self, capital_stake: CapitalStakeClient):
        self.capital_stake = capital_stake
        self.settings = get_settings()
        self._cache = get_memory_cache()

    def is_configured(self) -> bool:
        return self.capital_stake.is_configured()

    def missing_config(self) -> list[str]:
        if not self.capital_stake.is_configured():
            return ["CAPITAL_STAKE_UAT_TOKEN or CAPITAL_STAKE_API_KEY"]
        return []

    async def _require_configured(self) -> None:
        if not self.is_configured():
            raise ExternalServiceError(
                "Capital Stake", "API token not configured", error_code="SERVICE_UNAVAILABLE",
            )

    async def _cached(self, key: str, ttl: int, factory):
        cached = self._cache.get(key)
        if cached is not None:
            return cached[0], True, cached[1]
        await self._require_configured()
        try:
            result = await factory()
        except ExternalServiceError:
            stale = self._cache.get_stale(key)
            if stale is not None:
                return stale[0], True, stale[1]
            raise
        self._cache.set(key, result, ttl)
        return result, False, 0

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        await self._require_configured()
        return await self.capital_stake.get_company_profile(ticker)

    async def get_overview(self, ticker: str) -> tuple[CompanyOverviewResponse, bool, int]:
        cache_key = f"company:overview:{ticker.upper()}"

        async def fetch():
            return await self.capital_stake.get_company_overview(ticker)

        return await self._cached(cache_key, OVERVIEW_CACHE_TTL, fetch)

    async def get_profile(self, ticker: str) -> CompanyProfileResponse:
        cache_key = f"company:profile:{ticker.upper()}"

        async def fetch():
            return await self.capital_stake.get_profile(ticker)

        result, _, _ = await self._cached(cache_key, PROFILE_CACHE_TTL, fetch)
        return result

    async def get_statistics(
        self, ticker: str, user: Optional[dict[str, Any]] = None,
    ) -> tuple[CompanyStatisticsResponse, bool, int]:
        tier = get_user_tier(user)
        cache_key = f"company:statistics:{ticker.upper()}:{tier}"

        async def fetch():
            quote = self.capital_stake._unwrap_data(await self.capital_stake.get_single_quote(ticker))
            metrics = self.capital_stake._unwrap_data(await self.capital_stake.get_financial_data(ticker))
            return map_statistics(ticker, quote, metrics, tier=tier)

        return await self._cached(cache_key, STATS_CACHE_TTL, fetch)

    async def get_earnings(self, ticker: str) -> tuple[EarningsResponse, bool, int]:
        cache_key = f"company:earnings:{ticker.upper()}"

        async def fetch():
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_key_metrics_quarterly(ticker))
            return map_earnings(ticker, raw)

        return await self._cached(cache_key, EARNINGS_CACHE_TTL, fetch)

    async def get_dividends(self, ticker: str) -> tuple[DividendResponse, bool, int]:
        cache_key = f"company:dividends:{ticker.upper()}"

        async def fetch():
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_dividends(ticker))
            return map_dividends(ticker, raw)

        return await self._cached(cache_key, DIVIDENDS_CACHE_TTL, fetch)

    async def get_ownership(self, ticker: str) -> tuple[OwnershipResponse, bool, int]:
        cache_key = f"company:ownership:{ticker.upper()}"

        async def fetch():
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_ownership(ticker))
            return map_ownership(ticker, raw)

        return await self._cached(cache_key, OWNERSHIP_CACHE_TTL, fetch)

    async def get_period_returns(self, ticker: str) -> tuple[PeriodReturnsResponse, bool, int]:
        cache_key = f"company:period_returns:{ticker.upper()}"

        async def fetch():
            validate_ohlcv_params("2y", "1d")
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_eod_data(ticker))
            ohlcv = map_ohlcv(ticker, raw, "2y", "1d")
            return compute_period_returns(ticker, ohlcv.points)

        return await self._cached(cache_key, PERIOD_RETURNS_CACHE_TTL, fetch)

    async def get_faq(self, ticker: str) -> tuple[FaqResponse, bool, int]:
        cache_key = f"company:faq:{ticker.upper()}"

        async def fetch():
            quote = await self.capital_stake.get_stock_quote(ticker)
            return map_faq(ticker, quote.name, quote.price, quote.currency)

        return await self._cached(cache_key, FAQ_CACHE_TTL, fetch)
