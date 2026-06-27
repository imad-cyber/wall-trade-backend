"""Company profile service."""
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.domain.company.models import CompanyProfile
from app.providers.capital_stake.client import CapitalStakeClient


class CompanyService:
    def __init__(self, capital_stake: CapitalStakeClient):
        self.capital_stake = capital_stake
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.capital_stake_key)

    def missing_config(self) -> list[str]:
        if not self.settings.capital_stake_key:
            return ["CAPITAL_STAKE_API_KEY or CAPITAL_API_KEY"]
        return []

    async def get_company_profile(self, ticker: str) -> CompanyProfile:
        if not self.is_configured():
            raise ExternalServiceError(
                "Capital Stake",
                "API key not configured",
                error_code="CAPITAL_STAKE_NOT_CONFIGURED",
            )
        return await self.capital_stake.get_company_profile(ticker)
