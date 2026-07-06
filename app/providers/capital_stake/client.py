"""Capital Stake (csapis.com) API client."""
from typing import Any, Optional

import httpx

from app.api.v1.schemas.company import CompanyOverviewResponse, CompanyProfileResponse, StockDataSchema
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError, ResourceNotFoundError
from app.core.http import get_http_client
from app.domain.company.models import CompanyProfile
from app.providers.capital_stake.mapper import map_overview, map_profile_basic, map_quote_to_stock_data


class CapitalStakeClient:
    """HTTP client for csapis.com market data."""

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
        return await self._get_json(f"/quotes/{ticker.upper()}")

    async def get_symbol_overview(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/symbols/{ticker.upper()}")

    async def get_company_profile_basic(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/company/profile/basic/{ticker.upper()}")

    async def get_stock_quote(self, ticker: str) -> StockDataSchema:
        quote = await self.get_single_quote(ticker)
        return map_quote_to_stock_data(ticker, self._unwrap_data(quote))

    async def get_company_overview(self, ticker: str) -> CompanyOverviewResponse:
        quote_raw, profile_raw = await self._fetch_quote_and_profile(ticker)
        return map_overview(ticker, quote_raw, profile_raw)

    async def get_profile(self, ticker: str) -> CompanyProfileResponse:
        raw = await self.get_company_profile_basic(ticker)
        return map_profile_basic(ticker, self._unwrap_data(raw))

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        """Legacy domain model — used by existing /company/{ticker} route."""
        overview = await self.get_company_overview(ticker)
        return CompanyProfile(
            ticker=overview.ticker,
            name=overview.name,
            description=None,
        )

    async def get_financial_data(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/key-metrics/annual/{ticker.upper()}")

    async def get_key_metrics_quarterly(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/key-metrics/quarterly/{ticker.upper()}")

    async def get_eod_data(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/stocks/eod/{ticker.upper()}")

    async def get_company_news(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/news/company/{ticker.upper()}")

    async def get_sector_news(self, sector: str = "all") -> dict[str, Any]:
        return await self._get_json(f"/news/sector/{sector}")

    async def get_dividends(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/payouts/{ticker.upper()}")

    async def get_ownership(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/ownership/{ticker.upper()}")

    async def get_all_tickers(self) -> dict[str, Any]:
        return await self._get_json("/symbols")

    async def get_indices(self) -> dict[str, Any]:
        return await self._get_json("/indices")

    async def get_index(self, index_id: str) -> dict[str, Any]:
        return await self._get_json(f"/indices/{index_id}")

    async def get_market_status(self) -> dict[str, Any]:
        return await self._get_json("/market/status")

    async def get_market_summary(self) -> dict[str, Any]:
        return await self._get_json("/market/summary")

    async def get_sector_constituents(self, sector: str) -> dict[str, Any]:
        return await self._get_json(f"/sectors/{sector}/constituents")

    async def get_technicals(self, ticker: str) -> dict[str, Any]:
        return await self._get_json(f"/technicals/{ticker.upper()}")

    async def _fetch_quote_and_profile(
        self, ticker: str,
    ) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
        quote_raw = self._unwrap_data(await self.get_single_quote(ticker))
        profile_raw: Optional[dict[str, Any]] = None
        try:
            profile_raw = self._unwrap_data(await self.get_company_profile_basic(ticker))
        except (ExternalServiceError, ResourceNotFoundError):
            try:
                profile_raw = self._unwrap_data(await self.get_symbol_overview(ticker))
            except (ExternalServiceError, ResourceNotFoundError):
                profile_raw = None
        return quote_raw, profile_raw

    async def _get_json(self, path: str) -> dict[str, Any]:
        try:
            return await self._http.get(path)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ResourceNotFoundError(f"Ticker {path.split('/')[-1]}") from exc
            raise ExternalServiceError(
                "Capital Stake",
                str(exc),
                error_code="PROVIDER_ERROR",
            ) from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                "Capital Stake",
                str(exc),
                error_code="PROVIDER_ERROR",
            ) from exc

    @staticmethod
    def _unwrap_data(raw: dict[str, Any]) -> dict[str, Any]:
        if isinstance(raw.get("data"), dict):
            return raw["data"]
        if isinstance(raw.get("result"), dict):
            return raw["result"]
        return raw
