"""Narrative intelligence response schemas."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class NarrativeTickerListResponse(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    count: int = 0


class HeroStatsResponse(BaseModel):
    total_narratives_monitored: int = 0
    active_coordination_flags: int = 0
    traps_detected_30d: int = 0
    avg_vms_score: float = 0.0
    market_health_score: float = 0.0
    snapshot_date: str = ""


class InfluenceNode(BaseModel):
    id: str
    out: int = 0
    in_: int = Field(0, alias="in")
    total: int = 0
    ratio: float = 0.0
    n: int = 0
    nrs: float = 0.0
    traps: int = 0

    model_config = {"populate_by_name": True}


class InfluenceEdge(BaseModel):
    source: str
    target: str
    weight: float = 0.0
    themes: str = ""
    contagion: float = 0.0
    chain: str = ""
    trap: Optional[str] = None


class InfluenceNetworkResponse(BaseModel):
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[InfluenceEdge] = Field(default_factory=list)


class UnifiedTickerNarrativeResponse(BaseModel):
    ticker: str
    data: dict[str, Any] = Field(default_factory=dict)


class NarrativeTimelineResponse(BaseModel):
    ticker: str
    stories: list[dict[str, Any]] = Field(default_factory=list)
    earnings: list[dict[str, Any]] = Field(default_factory=list)
    opex_dates: list[str] = Field(default_factory=list)
    price_history: list[dict[str, Any]] = Field(default_factory=list)
