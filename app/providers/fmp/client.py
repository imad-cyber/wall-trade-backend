"""FMP API client for macro indicators."""
from typing import Any

from app.core.config import get_settings
from app.core.http import get_http_client


class FMPClient:
    def __init__(self, http=None):
        settings = get_settings()
        self._http = http or get_http_client(
            "fmp",
            settings.FMP_BASE_URL,
            api_key=settings.FMP_API_KEY,
        )

    async def get_macro_indicators(self) -> dict[str, Any]:
        return await self._http.get("/economic", params={"apikey": get_settings().FMP_API_KEY})
