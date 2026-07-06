"""Symbol universe repository."""
from typing import Any

from app.repositories.base import BaseRepository


class SymbolRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "symbol_universe")

    def search(self, query: str, *, exchange: str = "PSX", limit: int = 10) -> list[dict[str, Any]]:
        q = query.upper()
        response = self._execute(
            self.db.table(self.table_name)
            .select("*")
            .ilike("ticker", f"{q}%")
            .eq("exchange", exchange)
            .limit(limit),
            operation="search",
        )
        return self._data(response) or []
