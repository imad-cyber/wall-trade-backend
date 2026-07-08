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
from app.providers.capital_stake.psx_symbols import KNOWN_INDEX_SYMBOLS, fallback_symbol_rows
from app.providers.capital_stake.v3_paths import TICKER_LIST_PATHS, financial_statement_path, lookback_days_for_range


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
        """Single Quote (#4) — /market/quote; falls back to Single Symbol Overview (#2) — /market/stock."""
        upper = ticker.upper()
        for path in ("/market/quote", "/market/stock"):
            try:
                raw = await self._get_json(path, params={"symbol": upper})
                row = self._normalize_row(self._unwrap_data(raw))
                if row:
                    return {"status": raw.get("status", "ok"), "data": row}
            except (ExternalServiceError, ResourceNotFoundError):
                continue
        return {"status": "ok", "data": {}}

    async def get_stock_overview_raw(self, ticker: str) -> dict[str, Any]:
        """Single Symbol Overview (#2) — /market/stock; always explicit call."""
        upper = ticker.upper()
        raw = await self._get_json("/market/stock", params={"symbol": upper})
        return self._normalize_row(self._unwrap_data(raw))

    async def get_symbol_overview(self, ticker: str) -> dict[str, Any]:
        return await self.get_single_quote(ticker)

    async def get_company_profile_basic(self, ticker: str) -> dict[str, Any]:
        """Company Profile Basic (#16) — /company/profile/overview; falls back to single quote."""
        upper = ticker.upper()
        try:
            raw = await self._get_json("/company/profile/overview", params={"symbol": upper})
            row = self._normalize_row(self._unwrap_data(raw))
            if row:
                return {"status": raw.get("status", "ok"), "data": row}
        except (ExternalServiceError, ResourceNotFoundError):
            pass
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
        """Key Metrics — Annual (#14) or Quarterly (#15).
        Full income/balance/cashflow statements are not in the subscribed plan;
        key-metrics data is returned for all statement_type values.
        """
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
        """EOD Unadjusted (#8) — /market/eod with date_from / date_to params."""
        end = to_date or date.today().isoformat()
        start = from_date or (date.today() - timedelta(days=lookback_days)).isoformat()
        return await self._get_json(
            "/market/eod",
            params={"symbol": ticker.upper(), "date_from": start, "date_to": end},
        )

    async def get_eod_for_range(self, ticker: str, range_: str = "2y") -> dict[str, Any]:
        return await self.get_eod_data(ticker, lookback_days=lookback_days_for_range(range_))

    def _news_date_range(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        lookback_days: int = 30,
    ) -> tuple[str, str]:
        end = date_to or date.today().isoformat()
        start = date_from or (date.today() - timedelta(days=lookback_days)).isoformat()
        return start, end

    async def get_company_news(
        self,
        ticker: str,
        *,
        offset: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        start, end = self._news_date_range(date_from=date_from, date_to=date_to)
        params: dict[str, Any] = {
            "symbol": ticker.upper(),
            "date_from": start,
            "date_to": end,
        }
        if offset is not None:
            params["offset"] = offset
        return await self._get_json("/news/company", params=params)

    async def get_sector_news(
        self,
        sector: str = "all",
        *,
        offset: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        sector_code = sector
        if sector.lower() == "all":
            sector_code = await self._default_sector_code()
        start, end = self._news_date_range(date_from=date_from, date_to=date_to)
        params: dict[str, Any] = {
            "sector_code": sector_code,
            "date_from": start,
            "date_to": end,
        }
        if offset is not None:
            params["offset"] = offset
        return await self._get_json("/news/sector", params=params)

    async def get_dividends(self, ticker: str) -> dict[str, Any]:
        """Dividends endpoint not in current subscription — returns empty."""
        return {"status": "ok", "data": []}

    async def get_ownership(self, ticker: str) -> dict[str, Any]:
        """Shareholder data not in current subscription — returns empty."""
        return {"status": "ok", "data": []}

    async def get_analyst_targets(self, ticker: str) -> dict[str, Any]:
        """Analyst targets not in current subscription — returns empty."""
        return {"status": "ok", "data": []}

    async def get_consensus_ratings(self, ticker: str) -> dict[str, Any]:
        """Consensus ratings not in current subscription — returns empty."""
        return {"status": "ok", "data": []}

    async def get_all_tickers(self) -> dict[str, Any]:
        rows = await self._fetch_ticker_list()
        if rows:
            stocks = [row for row in rows if not self._is_index_row(row)]
            if stocks:
                return {"status": "ok", "data": stocks}
        return {"status": "ok", "data": fallback_symbol_rows()}

    async def get_sectors(self) -> dict[str, Any]:
        return await self._get_json("/market/sectors")

    async def get_indices(self) -> dict[str, Any]:
        rows = await self._fetch_ticker_list(index_only=True)
        if rows:
            return {"status": "ok", "data": rows}
        rows = await self._fetch_index_quotes()
        if rows:
            return {"status": "ok", "data": rows}
        return {"status": "ok", "data": []}

    async def get_index(self, index_id: str) -> dict[str, Any]:
        """Single Index Overview (#7) — /market/index?code=<code>."""
        upper = index_id.upper()
        try:
            raw = await self._get_json("/market/index", params={"code": upper})
            row = self._normalize_row(self._unwrap_data(raw))
            if row:
                return {"status": raw.get("status", "ok"), "data": row}
        except (ExternalServiceError, ResourceNotFoundError):
            pass
        # Fallback: scan indices list
        raw = await self.get_indices()
        indices = self._unwrap_data(raw)
        if isinstance(indices, list):
            for row in indices:
                if not isinstance(row, dict):
                    continue
                symbol = str(
                    row.get("code") or row.get("s") or row.get("symbol") or ""
                ).upper()
                if symbol == upper:
                    return {"status": "ok", "data": row}
        raise ResourceNotFoundError(f"Index {index_id}")

    async def get_market_status(self) -> dict[str, Any]:
        return await self._get_json("/market/state")

    async def get_market_summary(self) -> dict[str, Any]:
        return await self.get_market_status()

    async def get_sector_constituents(self, sector: str) -> dict[str, Any]:
        """Return stocks in a given sector by filtering the All Stocks (#3) response."""
        try:
            raw = await self._get_json("/market/stocks")
            rows = self._rows_from_payload(self._unwrap_data(raw))
            sector_upper = str(sector).upper()
            filtered = [
                row for row in rows
                if isinstance(row, dict) and str(row.get("sector", "")).upper() == sector_upper
            ]
            return {"status": "ok", "data": filtered}
        except ExternalServiceError:
            return {"status": "ok", "data": []}

    async def get_technicals(self, ticker: str, interval: str = "1d") -> dict[str, Any]:
        """Technicals by Symbols (#20) — /market/technicals (symbol + interval required)."""
        return await self._get_json(
            "/market/technicals",
            params={"symbol": ticker.upper(), "interval": interval},
        )

    async def _all_sector_codes(self) -> list[str]:
        codes: list[str] = []
        try:
            raw = self._unwrap_data(await self.get_sectors())
            if isinstance(raw, list):
                for row in raw:
                    if not isinstance(row, dict):
                        continue
                    code = row.get("code") or row.get("sector_code") or row.get("id")
                    if code:
                        codes.append(str(code))
        except ExternalServiceError:
            pass
        return codes or ["0801"]

    async def _default_sector_code(self) -> str:
        codes = await self._all_sector_codes()
        return codes[0]

    async def _merge_live_ticker(self, ticker: str, quote_raw: dict[str, Any]) -> dict[str, Any]:
        """Enrich quote with live ticker row when available; never fail the caller."""
        if not quote_raw:
            return quote_raw
        try:
            tickers = self._unwrap_data(await self.get_all_tickers())
            if isinstance(tickers, list):
                target = ticker.upper()
                for row in tickers:
                    if not isinstance(row, dict):
                        continue
                    symbol = str(row.get("s", row.get("symbol", row.get("ticker", "")))).upper()
                    market_type = row.get("m")
                    if symbol == target and (market_type in (None, "REG") or market_type == "REG"):
                        return {**quote_raw, **row}
        except (ExternalServiceError, ResourceNotFoundError):
            pass
        return quote_raw

    async def _fetch_quote_and_profile(
        self, ticker: str,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        quote_raw = self._normalize_row(self._unwrap_data(await self.get_single_quote(ticker)))
        quote_raw = await self._merge_live_ticker(ticker, quote_raw)
        return quote_raw, quote_raw

    async def _fetch_ticker_list(self, *, index_only: bool = False) -> list[dict[str, Any]]:
        for path in TICKER_LIST_PATHS:
            try:
                raw = await self._get_json(path)
            except ExternalServiceError:
                continue
            rows = self._rows_from_payload(self._unwrap_data(raw))
            if not rows:
                continue
            if index_only:
                if path == "/market/indices":
                    return rows
                indices = [row for row in rows if self._is_index_row(row)]
                if indices:
                    return indices
                continue
            return rows
        return []

    async def _fetch_index_quotes(self) -> list[dict[str, Any]]:
        indices: list[dict[str, Any]] = []
        for symbol in KNOWN_INDEX_SYMBOLS:
            try:
                row = self._normalize_row(self._unwrap_data(await self.get_single_quote(symbol)))
            except (ExternalServiceError, ResourceNotFoundError):
                continue
            if not row:
                continue
            row = dict(row)
            row.setdefault("symbol", symbol)
            row.setdefault("s", symbol)
            row["m"] = "IDX"
            indices.append(row)
        return indices

    @staticmethod
    def _normalize_row(data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            rows = [row for row in data if isinstance(row, dict)]
            if not rows:
                return {}
            return rows[-1]
        return {}

    @staticmethod
    def _rows_from_payload(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            for key in ("data", "result", "rows", "items", "tickers", "indices"):
                val = data.get(key)
                if isinstance(val, list):
                    return [row for row in val if isinstance(row, dict)]
        return []

    @staticmethod
    def _is_index_row(row: dict[str, Any]) -> bool:
        if row.get("m") == "IDX":
            return True
        symbol = str(
            row.get("symbol", row.get("s", row.get("ticker", row.get("code", ""))))
        ).upper()
        if symbol in KNOWN_INDEX_SYMBOLS:
            return True
        if row.get("code") and row.get("close") is not None and not row.get("symbol") and not row.get("s"):
            return True
        row_type = row.get("type")
        return row_type in (0, 2, "2", "index", "IDX")

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
                symbol = (params or {}).get("symbol")
                if symbol:
                    raise ResourceNotFoundError(f"Ticker {symbol}") from exc
                raise ExternalServiceError(
                    "Capital Stake",
                    f"Endpoint not found: '{path}'",
                    error_code="PROVIDER_ERROR",
                ) from exc
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
