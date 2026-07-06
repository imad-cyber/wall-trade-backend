"""Market data response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OHLCVPoint(BaseModel):
    date: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: int = 0


class OHLCVResponse(BaseModel):
    ticker: str
    currency: str = "PKR"
    exchange: str = "PSX"
    range: str
    interval: str
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    points: list[OHLCVPoint] = Field(default_factory=list)


class PeerMetricPositions(BaseModel):
    sector: int = 50
    subject: int = 50
    peers: int = 50


class PeerMetric(BaseModel):
    metric: str
    subject: str
    peers: str
    sector: str
    positions: PeerMetricPositions


class PeersComparisonResponse(BaseModel):
    ticker: str
    sector: str = "Unknown"
    peers: list[str] = Field(default_factory=list)
    categories: list[str] = Field(
        default_factory=lambda: ["Value", "Quote", "Size", "Growth", "Profit"]
    )
    metrics: list[PeerMetric] = Field(default_factory=list)


class RelatedTickerItem(BaseModel):
    name: str
    ticker: str
    price: float
    change_percent: float


class RelatedTickersResponse(BaseModel):
    ticker: str
    related: list[RelatedTickerItem] = Field(default_factory=list)


class OpexDatesResponse(BaseModel):
    ticker: str
    opex_dates: list[str] = Field(default_factory=list)


class MarketSummaryIndex(BaseModel):
    name: str
    symbol: str
    price: float
    currency: str = "PKR"
    change_percent: float = 0.0
    is_delayed: bool = False


class MarketSummaryChartPoint(BaseModel):
    time: str
    value: float


class MarketSummaryResponse(BaseModel):
    featured_index: MarketSummaryIndex
    chart_data: list[MarketSummaryChartPoint] = Field(default_factory=list)
    major_indices: list[MarketSummaryIndex] = Field(default_factory=list)
    market_status: str = "Closed"
    last_updated: str
