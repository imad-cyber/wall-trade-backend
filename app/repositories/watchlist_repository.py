"""Watchlist repository — Supabase user_watchlist table."""
from typing import Any, Optional

from app.repositories.base import BaseRepository


class WatchlistRepository(BaseRepository):
    MAX_ITEMS = 50

    def __init__(self, db_client):
        super().__init__(db_client, "user_watchlist")

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .order("position"),
            operation="list_for_user",
        )
        return self._data(response) or []

    def add(self, user_id: str, ticker: str, position: int) -> dict[str, Any]:
        return self.create({
            "user_id": user_id,
            "ticker": ticker.upper(),
            "position": position,
        })

    def remove(self, user_id: str, ticker: str) -> bool:
        response = self._execute(
            self.db.table(self.table_name)
            .delete()
            .eq("user_id", user_id)
            .eq("ticker", ticker.upper()),
            operation="remove",
        )
        rows = self._data(response) or []
        return bool(rows)

    def find_item(self, user_id: str, ticker: str) -> Optional[dict[str, Any]]:
        rows = self.list(limit=1, filters={"user_id": user_id, "ticker": ticker.upper()})
        return rows[0] if rows else None

    def reorder(self, user_id: str, tickers: list[str]) -> list[dict[str, Any]]:
        for idx, ticker in enumerate(tickers):
            self.update(
                ticker.upper(),
                {"position": idx},
                id_column="ticker",
            )
        return self.list_for_user(user_id)
