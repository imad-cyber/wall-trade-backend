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
from app.providers.capital_stake.mapper import _to_float
from app.providers.capital_stake.extended_mapper import (
    _extract_key_metric,
    _normalize_key_metrics_raw,
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
            metrics: dict[str, Any] = {}
            try:
                metrics = self.capital_stake._unwrap_data(await self.capital_stake.get_consensus_ratings(ticker))
                earnings = metrics.get("earnings") if isinstance(metrics.get("earnings"), dict) else {}
                valuation = metrics.get("valuation") if isinstance(metrics.get("valuation"), dict) else {}
                dividend = metrics.get("dividend") if isinstance(metrics.get("dividend"), dict) else {}
                metrics = {
                    **quote,
                    **earnings,
                    **valuation,
                    **dividend,
                    "pe_current": valuation.get("pe_current"),
                    "yield_estimate": dividend.get("yield_estimate"),
                }
            except ExternalServiceError:
                metrics = dict(quote)

            annual_raw: Any = None
            try:
                annual_raw = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_financial_statement(ticker, "income", "annual")
                )
            except ExternalServiceError:
                pass

            if annual_raw:
                pe = _extract_key_metric(annual_raw, "price earnings ratio")
                if pe is None:
                    pe = _extract_key_metric(annual_raw, "price to earnings")
                metrics["pe_ratio"] = metrics.get("pe_ratio") or pe
                metrics["returnOnEquity"] = (
                    metrics.get("returnOnEquity") or _extract_key_metric(annual_raw, "return on equity")
                )
                metrics["returnOnAssets"] = (
                    metrics.get("returnOnAssets") or _extract_key_metric(annual_raw, "return on assets")
                )
                metrics["book_value"] = _extract_key_metric(annual_raw, "book value per share")
                metrics["revenue"] = metrics.get("revenue") or _extract_key_metric(annual_raw, "sales")
                metrics["eps"] = metrics.get("eps") or _extract_key_metric(annual_raw, "earnings per share")
                div_yield = _extract_key_metric(annual_raw, "dividend yield")
                if div_yield is not None and not metrics.get("dividendYield"):
                    metrics["dividendYield"] = f"{_to_float(div_yield):.2f}%"

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
            stub_raw = self.capital_stake._unwrap_data(await self.capital_stake.get_dividends(ticker))
            stub_rows = stub_raw if isinstance(stub_raw, list) else []

            annual_rows: list[dict[str, Any]] = []
            latest_price = 0.0
            try:
                annual_resp = self.capital_stake._unwrap_data(
                    await self.capital_stake.get_financial_statement(ticker, "income", "annual")
                )
                annual_rows = _normalize_key_metrics_raw(annual_resp)
                quote = self.capital_stake._unwrap_data(await self.capital_stake.get_single_quote(ticker))
                from app.providers.capital_stake.mapper import _first

                latest_price = _to_float(_first(quote, "lastPrice", "price"), 0.0)
            except ExternalServiceError:
                pass

            synthetic_rows: list[dict[str, Any]] = []
            if annual_rows:
                for row in annual_rows:
                    if "dividend per share" not in str(row.get("name", "")).lower():
                        continue
                    period = str(row.get("period", "")).upper()
                    if period == "TTM":
                        continue
                    dps_val = row.get("value")
                    if dps_val is not None:
                        synthetic_rows.append({
                            "date": str(row.get("period", "")),
                            "amount": dps_val,
                            "type": "annual",
                        })
                synthetic_rows.sort(
                    key=lambda item: str(item.get("date", "")),
                    reverse=True,
                )

            dividend_rows = stub_rows if stub_rows else synthetic_rows
            payout_ratio = _extract_key_metric(annual_rows, "payout ratio") if annual_rows else None
            if payout_ratio is None and annual_rows:
                payout_ratio = _extract_key_metric(annual_rows, "cash payout ratio")

            dividend_yield: str | None = None
            if synthetic_rows and latest_price:
                try:
                    latest_dps = float(synthetic_rows[0].get("amount", 0))
                    if latest_dps and latest_price:
                        dividend_yield = f"{latest_dps / latest_price * 100:.2f}%"
                except (TypeError, ValueError):
                    pass
            if not dividend_yield and annual_rows:
                raw_yield = _extract_key_metric(annual_rows, "dividend yield")
                if raw_yield is not None:
                    dividend_yield = f"{_to_float(raw_yield):.2f}%"

            enriched_raw: dict[str, Any] = {
                "data": dividend_rows,
                "payoutRatio": payout_ratio,
                "dividendYield": dividend_yield,
                "annualizedPayout": synthetic_rows[0].get("amount") if synthetic_rows else None,
                "frequency": "annual",
            }
            return map_dividends(ticker, enriched_raw)

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
            raw = self.capital_stake._unwrap_data(
                await self.capital_stake.get_eod_for_range(ticker, "2y")
            )
            ohlcv = map_ohlcv(ticker, raw, "2y", "1d")
            return compute_period_returns(ticker, ohlcv.points)

        return await self._cached(cache_key, PERIOD_RETURNS_CACHE_TTL, fetch)

    async def get_faq(self, ticker: str) -> tuple[FaqResponse, bool, int]:
        cache_key = f"company:faq:{ticker.upper()}"

        async def fetch():
            quote = await self.capital_stake.get_stock_quote(ticker)
            return map_faq(ticker, quote.name, quote.price, quote.currency)

        return await self._cached(cache_key, FAQ_CACHE_TTL, fetch)
