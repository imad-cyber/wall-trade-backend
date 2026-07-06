"""Watchlist service — W1 through W4."""
from datetime import datetime, timezone
from typing import Any

from app.api.v1.schemas.watchlist import WatchlistItem
from app.core.exceptions import ConflictError, ResourceNotFoundError, ValidationError
from app.repositories.watchlist_repository import WatchlistRepository
from app.services.market_service import MarketService


class WatchlistService:
    def __init__(self, repo: WatchlistRepository, market_service: MarketService):
        self.repo = repo
        self.market = market_service

    async def _enrich(self, row: dict[str, Any]) -> WatchlistItem:
        ticker = row["ticker"]
        try:
            quote, _, _ = await self.market.get_quote(ticker)
            return WatchlistItem(
                ticker=ticker,
                name=quote.name,
                price=quote.price,
                change=quote.change,
                change_percent=quote.change_percent,
                added_at=row.get("added_at", datetime.now(timezone.utc).isoformat()),
            )
        except Exception:
            return WatchlistItem(
                ticker=ticker,
                name=ticker,
                price=0.0,
                change=0.0,
                change_percent=0.0,
                added_at=row.get("added_at", datetime.now(timezone.utc).isoformat()),
            )

    async def get_watchlist(self, user_id: str) -> list[WatchlistItem]:
        rows = self.repo.list_for_user(user_id)
        return [await self._enrich(r) for r in rows]

    async def add_to_watchlist(self, user_id: str, ticker: str) -> WatchlistItem:
        existing = self.repo.find_item(user_id, ticker)
        if existing:
            raise ConflictError(f"{ticker} already in watchlist", error_code="CONFLICT")
        items = self.repo.list_for_user(user_id)
        if len(items) >= WatchlistRepository.MAX_ITEMS:
            raise ValidationError("Watchlist limit exceeded", error_code="VALIDATION_ERROR")
        row = self.repo.add(user_id, ticker, position=len(items))
        return await self._enrich(row)

    async def remove_from_watchlist(self, user_id: str, ticker: str) -> str:
        if not self.repo.remove(user_id, ticker):
            raise ResourceNotFoundError(f"Watchlist item {ticker}")
        return ticker.upper()

    async def reorder(self, user_id: str, tickers: list[str]) -> list[WatchlistItem]:
        self.repo.reorder(user_id, tickers)
        return await self.get_watchlist(user_id)
