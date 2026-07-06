"""Analysis response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AnalystConsensus(BaseModel):
    total: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    label: str = "Hold"
    price_target: Optional[float] = None
    upside_percent: Optional[float] = None


class AnalystRating(BaseModel):
    firm: str
    position: Literal["Buy", "Hold", "Sell"] = "Hold"
    price_target: Optional[float] = None
    upside_percent: Optional[float] = None
    from_price_target: Optional[float] = None
    action: str = "Maintain"
    date: str


class AnalystResponse(BaseModel):
    ticker: str
    consensus: AnalystConsensus
    ratings: list[AnalystRating] = Field(default_factory=list)
    total_ratings: int = 0
    page: int = 1
    page_size: int = 10


class SwotItem(BaseModel):
    category: Literal["STRENGTH", "WEAKNESS", "OPPORTUNITY", "THREAT"]
    label: str
    description: str
    icon: str = "shield"


class SwotResponse(BaseModel):
    ticker: str
    generated_at: str
    items: list[SwotItem] = Field(default_factory=list)


class TechnicalTimeframe(BaseModel):
    id: str
    label: str
    signal: Optional[str] = None
    signal_type: Optional[Literal["sell", "neutral", "buy", "strongBuy"]] = None
    locked: bool = False


class TechnicalAnalysisResponse(BaseModel):
    ticker: str
    snapshot_at: str
    overall_signal: str = "Neutral"
    timeframes: list[TechnicalTimeframe] = Field(default_factory=list)


class EarningsCallResponse(BaseModel):
    ticker: str
    quarter: str = ""
    call_date: str = ""
    last_updated: str = ""
    bullets: list[str] = Field(default_factory=list)
