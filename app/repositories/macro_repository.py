"""Macro cache repository."""
from typing import Optional

from app.domain.macro.models import MacroCache
from app.repositories.base import BaseRepository


class MacroRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "macro_cache")

    def get_latest(self) -> Optional[MacroCache]:
        rows = self.list(limit=1, order_by="updated_at", desc=True)
        return MacroCache.from_db_row(rows[0]) if rows else None
