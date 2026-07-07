"""Capital Stake (csapis.com) API v3 client."""
from datetime import date, timedelta
from typing import Any, Optional

import httpx

from app.api.v1.schemas.company import CompanyOverviewResponse, CompanyProfileResponse, StockDataSchema
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, ResourceNotFoundError
from app.core.http import get_http_client
from app.domain.company.models import CompanyProfile
from app.providers.capital_stake.mapper import map_overview, map_profile_basic, map_quote_to_stock_data
from app.providers.capital_stake.v3_paths import financial_statement_path, lookback_days_for_range


class CapitalStakeClient:
    """HTTP client for csapis.com market data (API v3)."""

    def __init__(self, http=None):
        settings = get_settings()
        token = settings.capital_stake_token
        self._http = http or get_http_client(
            "capital_stake",
            settings.capital_stake_base_url,
            api_key=token,
        )

    def is_configured(self) -> bool:
        return bool(get_settings().capital_stake_token)

    async def get_single_quote(self, ticker: str) -> dict[str, Any]:
        return await self._get_json("/market/stock", params={"symbol": ticker.upper()})

    async def get_symbol_overview(self, ticker: str) -> dict[str, Any]:
        return await self.get_single_quote(ticker)

    async def get_company_profile_basic(self, ticker: str) -> dict[str, Any]:
        return await self.get_single_quote(ticker)

    async def get_stock_quote(self, ticker: str) -> StockDataSchema:
        quote_raw = self._unwrap_data(await self.get_single_quote(ticker))
        quote_raw = await self._merge_live_ticker(ticker, quote_raw)
        return map_quote_to_stock_data(ticker, quote_raw)

    async def get_company_overview(self, ticker: str) -> CompanyOverviewResponse:
        quote_raw, profile_raw = await self._fetch_quote_and_profile(ticker)
        return map_overview(ticker, quote_raw, profile_raw)

    async def get_profile(self, ticker: str) -> CompanyProfileResponse:
        raw = await self.get_company_profile_basic(ticker)
        return map_profile_basic(ticker, self._unwrap_data(raw))

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        overview = await self.get_company_overview(ticker)
        return CompanyProfile(
            ticker=overview.ticker,
            name=overview.name,
            description=None,
        )

    async def get_financial_statement(
        self,
        ticker: str,
        statement_type: str,
        period: str,
    ) -> dict[str, Any]:
        path = financial_statement_path(statement_type, period)
        return await self._get_json(path, params={"symbol": ticker.upper()})

    async def get_financial_data(self, ticker: str) -> dict[str, Any]:
        return await self.get_financial_statement(ticker, "income", "annual")

    async def get_key_metrics_quarterly(self, ticker: str) -> dict[str, Any]:
        return await self.get_financial_statement(ticker, "income", "quarterly")

    async def get_eod_data(
        self,
        ticker: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
        lookback_days: int = 30,
    ) -> dict[str, Any]:
        end = to_date or date.today().isoformat()
        start = from_date or (date.today() - timedelta(days=lookback_days)).isoformat()
        return await self._get_json(
            "/market/eod-adj",
            params={"symbol": ticker.upper(), "from": start, "to": end},
        )

    async def get_eod_for_range(self, ticker: str, range_: str = "2y") -> dict[str, Any]:
        return await self.get_eod_data(ticker, lookback_days=lookback_days_for_range(range_))

    async def get_company_news(
        self,
        ticker: str,
        *,
        offset: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"symbol": ticker.upper()}
        if offset is not None:
            params["offset"] = offset
        return await self._get_json("/news/company", params=params)

    async def get_sector_news(self, sector: str = "all") -> dict[str, Any]:
        sector_code = sector
        if sector.lower() == "all":
            sector_code = await self._default_sector_code()
        return await self._get_json("/news/sector", params={"sector_code": sector_code})

    async def get_dividends(self, ticker: str) -> dict[str, Any]:
        return await self._get_json("/payouts/dividends", params={"symbol": ticker.upper()})

    async def get_ownership(self, ticker: str) -> dict[str, Any]:
        return await self._get_json("/company/shareholders", params={"symbol": ticker.upper()})

    async def get_analyst_targets(self, ticker: str) -> dict[str, Any]:
        return await self._get_json("/research/targets", params={"symbol": ticker.upper()})

    async def get_consensus_ratings(self, ticker: str) -> dict[str, Any]:
        return await self._get_json("/research/consensus", params={"symbol": ticker.upper()})

    async def get_all_tickers(self) -> dict[str, Any]:
        return await self._get_json("/market/tickers")

    async def get_sectors(self) -> dict[str, Any]:
        return await self._get_json("/market/sectors")

    async def get_indices(self) -> dict[str, Any]:
        raw = await self._get_json("/market/tickers")
        tickers = self._unwrap_data(raw)
        if isinstance(tickers, list):
            indices = [row for row in tickers if isinstance(row, dict) and row.get("m") == "IDX"]
            return {"status": raw.get("status", "ok"), "data": indices}
        return raw

    async def get_index(self, index_id: str) -> dict[str, Any]:
        raw = await self.get_indices()
        indices = self._unwrap_data(raw)
        if isinstance(indices, list):
            target = index_id.upper()
            for row in indices:
                if isinstance(row, dict) and str(row.get("s", "")).upper() == target:
                    return {"status": "ok", "data": row}
        raise ResourceNotFoundError(f"Index {index_id}")

    async def get_market_status(self) -> dict[str, Any]:
        return await self._get_json("/market/state")

    async def get_market_summary(self) -> dict[str, Any]:
        return await self.get_market_status()

    async def get_sector_constituents(self, sector: str) -> dict[str, Any]:
        for path in ("/market/sectors/stocks", "/market/sector/stocks"):
            try:
                return await self._get_json(path, params={"sector_code": sector})
            except ExternalServiceError as exc:
                if "404" in str(exc):
                    continue
                raise
        return {"status": "ok", "data": []}

    async def get_technicals(self, ticker: str, interval: str = "1d") -> dict[str, Any]:
        return await self._get_json(
            "/market/technicals",
            params={"symbol": ticker.upper(), "interval": interval},
        )

    async def _default_sector_code(self) -> str:
        try:
            raw = self._unwrap_data(await self.get_sectors())
            if isinstance(raw, list):
                for row in raw:
                    if not isinstance(row, dict):
                        continue
                    code = row.get("code") or row.get("sector_code") or row.get("id")
                    if code:
                        return str(code)
        except ExternalServiceError:
            pass
        return "0801"

    async def _merge_live_ticker(self, ticker: str, quote_raw: dict[str, Any]) -> dict[str, Any]:
        try:
            tickers = self._unwrap_data(await self.get_all_tickers())
            if isinstance(tickers, list):
                target = ticker.upper()
                for row in tickers:
                    if (
                        isinstance(row, dict)
                        and str(row.get("s", "")).upper() == target
                        and row.get("m") == "REG"
                    ):
                        return {**quote_raw, **row}
        except ExternalServiceError:
            pass
        return quote_raw

    async def _fetch_quote_and_profile(
        self, ticker: str,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        quote_raw = self._unwrap_data(await self.get_single_quote(ticker))
        quote_raw = await self._merge_live_ticker(ticker, quote_raw)
        return quote_raw, quote_raw

    async def _get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            return await self._http.get(path, params=params)
        except httpx.HTTPStatusError as exc:
            failed_url = str(exc.request.url) if exc.request else path
            status = exc.response.status_code
            if status == 404:
                symbol = (params or {}).get("symbol") or path.split("/")[-1]
                raise ResourceNotFoundError(f"Ticker {symbol}") from exc
            if status == 401:
                raise ExternalServiceError(
                    "Capital Stake",
                    "Authentication failed — verify CAPITAL_STAKE_UAT_TOKEN",
                    error_code="AUTH_ERROR",
                ) from exc
            if status == 403:
                raise ExternalServiceError(
                    "Capital Stake",
                    f"Subscription required for endpoint '{path}' — contact Capital Stake to enable this API",
                    error_code="SUBSCRIPTION_ERROR",
                ) from exc
            if status == 429:
                raise ExternalServiceError(
                    "Capital Stake",
                    "Rate limit exceeded — slow down requests or upgrade plan",
                    error_code="RATE_LIMITED",
                ) from exc
            raise ExternalServiceError(
                "Capital Stake",
                f"Provider returned {status} for '{failed_url}'",
                error_code="PROVIDER_ERROR",
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Capital Stake",
                str(exc),
                error_code="PROVIDER_ERROR",
            ) from exc

    @staticmethod
    def _unwrap_data(raw: dict[str, Any]) -> Any:
        data = raw.get("data")
        if data is not None:
            return data
        if isinstance(raw.get("result"), dict):
            return raw["result"]
        return raw
