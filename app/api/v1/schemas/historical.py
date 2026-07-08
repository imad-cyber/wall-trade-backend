"""Historical OHLCV response schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class HistoricalRow(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: int = 0
    change_percent: Optional[float] = None


class HistoricalDataResponse(BaseModel):
    ticker: str
    range: str
    interval: str
    rows: list[HistoricalRow] = Field(default_factory=list)
    total: int = 0
