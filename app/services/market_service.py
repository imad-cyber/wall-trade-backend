"""Market price service."""
from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.domain.market.models import Price
from app.providers.psx_proxy.client import PSXProxyClient


class MarketService:
    def __init__(self, psx_client: PSXProxyClient):
        self.psx_client = psx_client
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(self.settings.psx_proxy_base_url)

    def missing_config(self) -> list[str]:
        if not self.settings.psx_proxy_base_url:
            return ["PSX_PROXY_URL or PSX_PROXY_BASE_URL"]
        return []

    async def get_all_prices(self) -> list[Price]:
        if not self.is_configured():
            raise ExternalServiceError(
                "PSX Proxy",
                "URL not configured",
                error_code="PSX_PROXY_NOT_CONFIGURED",
            )
        return await self.psx_client.get_all_prices()

    async def get_price(self, ticker: str) -> Price:
        if not self.is_configured():
            raise ExternalServiceError(
                "PSX Proxy",
                "URL not configured",
                error_code="PSX_PROXY_NOT_CONFIGURED",
            )
        return await self.psx_client.get_price(ticker)
