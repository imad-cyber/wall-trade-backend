"""Macro data service."""
from typing import Optional

from app.domain.macro.models import MacroCache
from app.observability.metrics import record_cache_hit
from app.providers.fmp.client import FMPClient
from app.repositories.macro_repository import MacroRepository


class MacroService:
    def __init__(self, macro_repo: MacroRepository, fmp_client: Optional[FMPClient] = None):
        self.macro_repo = macro_repo
        self.fmp_client = fmp_client

    def get_latest(self) -> Optional[MacroCache]:
        macro = self.macro_repo.get_latest()
        if macro:
            record_cache_hit("macro")
        return macro

    async def fetch_from_provider(self) -> dict:
        if self.fmp_client is None:
            return {}
        return await self.fmp_client.get_macro_indicators()
