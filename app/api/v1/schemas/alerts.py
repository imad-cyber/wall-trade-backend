"""User alerts response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    id: str
    ticker: str
    alert_type: Literal["price_above", "price_below", "percent_change"]
    threshold: float
    is_active: bool = True
    created_at: str
    triggered_at: Optional[str] = None


class AlertCreateRequest(BaseModel):
    ticker: str
    alert_type: Literal["price_above", "price_below", "percent_change"]
    threshold: float


class AlertListResponse(BaseModel):
    alerts: list[AlertItem] = Field(default_factory=list)
