"""Capital Stake API client."""
from typing import Any

from app.core.config import get_settings
from app.core.http import get_http_client
from app.domain.company.models import CompanyProfile
from app.providers.capital_stake.mapper import CompanyMapper


class CapitalStakeClient:
    def __init__(self, http=None):
        settings = get_settings()
        base_url = settings.CAPITAL_STAKE_BASE_URL or "https://api.capitalstake.com"
        self._http = http or get_http_client(
            "capital_stake",
            base_url,
            api_key=settings.capital_stake_key,
        )

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        raw = await self._http.get(f"/company/{ticker.upper()}")
        return CompanyMapper.to_domain(ticker, raw)

    async def get_financial_data(self, ticker: str) -> dict[str, Any]:
        return await self._http.get(f"/company/{ticker.upper()}/financials")
