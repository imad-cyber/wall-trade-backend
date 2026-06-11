"""
Wall-Trade MVP request/response schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiResponse(BaseModel):
    """Standard documented response envelope."""

    success: bool = True
    message: str
    data: Any = None


class ServiceUnavailableResponse(BaseModel):
    """Response body for endpoints waiting on external service credentials."""

    success: bool = False
    message: str
    missing_configuration: list[str]


class AnalysisObject(BaseModel):
    """Structured AI analysis object stored in analysis_cache."""

    verdict: str
    summary: str
    analysis: list[str]
    key_factors: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class AnalysisCacheCreate(BaseModel):
    """Manual analysis-cache insert/update payload for admin or test usage."""

    ticker: str
    verdict: str
    summary: str
    analysis: dict[str, Any]
    expires_at: Optional[datetime] = None


class PortfolioCreate(BaseModel):
    client_id: int
    commodity_id: int
    sector_id: Optional[int] = None
    script_id: Optional[int] = None
    holding_volume: Optional[Decimal] = None
    holding_price_avg: Optional[Decimal] = None
    is_active: bool = True


class PortfolioUpdate(BaseModel):
    sector_id: Optional[int] = None
    script_id: Optional[int] = None
    holding_volume: Optional[Decimal] = None
    holding_price_avg: Optional[Decimal] = None
    is_active: Optional[bool] = None


class TradeCreate(BaseModel):
    client_id: int
    commodity_id: int
    trade_type: int
    confirm_date: datetime
    sector_id: Optional[int] = None
    script_id: Optional[int] = None
    trade_volume: Optional[Decimal] = None
    trade_price: Optional[Decimal] = None
    confirm_time: Optional[datetime] = None
    status: Optional[str] = None
    is_active: bool = True


class TradeUpdate(BaseModel):
    status: Optional[str] = None
    trade_volume: Optional[Decimal] = None
    trade_price: Optional[Decimal] = None
    is_active: Optional[bool] = None


class MarketFeelCreate(BaseModel):
    entry_date: datetime
    entry_time: Optional[datetime] = None
    commodity_id: Optional[int] = None
    booming_sector_id: Optional[int] = None
    loosing_sector_id: Optional[int] = None
    risk_score: Optional[Decimal] = None
    sentiments_text: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class SectorFeelCreate(BaseModel):
    entry_date: datetime
    title: str
    entry_time: Optional[datetime] = None
    commodity_id: Optional[int] = None
    trades: Optional[int] = None
    volume: Optional[int] = None
    risk_score: Optional[Decimal] = None
    sentiments_text: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class ScriptHistoryCreate(BaseModel):
    history_date: datetime
    commodity_id: int
    sector_id: int
    script_id: int
    close_price: Optional[Decimal] = None
    close_total_volume: Optional[int] = None
    close_total_trades: Optional[int] = None
    ai_risk_score: Optional[Decimal] = None
    ai_move_direction: Optional[Decimal] = None
    weekly_move_direction: Optional[Decimal] = None
    avg_price_30d: Optional[Decimal] = None
    avg_price_90d: Optional[Decimal] = None
    avg_price_180d: Optional[Decimal] = None


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
