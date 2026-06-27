"""Market domain models."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.domain.market.enums import MarketDirection


class Price(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    price: Decimal
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_provider_row(cls, raw: dict[str, Any]) -> "Price":
        ticker = raw.get("ticker") or raw.get("symbol") or ""
        return cls(
            ticker=str(ticker).upper(),
            price=Decimal(str(raw.get("price") or raw.get("last") or 0)),
            change=Decimal(str(raw["change"])) if raw.get("change") is not None else None,
            change_percent=Decimal(str(raw["change_percent"])) if raw.get("change_percent") is not None else None,
            volume=raw.get("volume"),
        )


class OHLCV(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    date: datetime


class MarketSentiment(BaseModel):
    model_config = ConfigDict(frozen=True)

    direction: MarketDirection
    score: Optional[Decimal] = None
    description: Optional[str] = None
