"""Financial statements service — F1, F2, F3."""
from app.api.v1.schemas.financials import FinancialStatementResponse
from app.core.exceptions import ExternalServiceError, ValidationError
from app.core.memory_cache import get_memory_cache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import map_financial_statement

CACHE_TTL = 86400


class FinancialsService:
    def __init__(self, capital_stake: CapitalStakeClient):
        self.capital_stake = capital_stake
        self._cache = get_memory_cache()

    async def _get_statement(
        self, ticker: str, statement_type: str, period: str, years: int,
    ) -> tuple[FinancialStatementResponse, bool, int]:
        if period not in ("annual", "quarterly"):
            raise ValidationError("period must be annual or quarterly")
        if not 1 <= years <= 20:
            raise ValidationError("years must be between 1 and 20")

        cache_key = f"financials:{ticker.upper()}:{statement_type}:{period}:{years}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached[0], True, cached[1]

        if not self.capital_stake.is_configured():
            raise ExternalServiceError(
                "Capital Stake", "API token not configured", error_code="SERVICE_UNAVAILABLE",
            )

        if period == "quarterly":
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_key_metrics_quarterly(ticker))
        else:
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_financial_data(ticker))

        result = map_financial_statement(ticker, raw, statement_type, period)
        result.rows = result.rows[:years]
        self._cache.set(cache_key, result, CACHE_TTL)
        return result, False, 0

    async def get_income_statement(self, ticker: str, period: str = "annual", years: int = 8):
        return await self._get_statement(ticker, "income", period, years)

    async def get_balance_sheet(self, ticker: str, period: str = "annual", years: int = 8):
        return await self._get_statement(ticker, "balance-sheet", period, years)

    async def get_cash_flow(self, ticker: str, period: str = "annual", years: int = 8):
        return await self._get_statement(ticker, "cash-flow", period, years)
