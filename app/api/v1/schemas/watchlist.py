"""Watchlist response schemas."""
from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    ticker: str
    name: str
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    added_at: str


class WatchlistAddRequest(BaseModel):
    ticker: str


class WatchlistRemoveResponse(BaseModel):
    removed: str


class WatchlistReorderRequest(BaseModel):
    tickers: list[str] = Field(default_factory=list)
