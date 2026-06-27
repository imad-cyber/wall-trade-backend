"""PSX Proxy API client."""
from app.core.config import get_settings
from app.core.http import get_http_client
from app.domain.market.models import Price
from app.providers.psx_proxy.mapper import PriceMapper


class PSXProxyClient:
    def __init__(self, http=None):
        settings = get_settings()
        base_url = settings.psx_proxy_base_url or "http://localhost:9000"
        self._http = http or get_http_client("psx_proxy", base_url)

    async def get_all_prices(self) -> list[Price]:
        raw = await self._http.get("/prices/all")
        items = raw if isinstance(raw, list) else raw.get("data") or raw.get("prices") or []
        return PriceMapper.to_domain_list(items)

    async def get_price(self, ticker: str) -> Price:
        raw = await self._http.get(f"/prices/{ticker.upper()}")
        return PriceMapper.to_domain(raw)
