"""Macro domain models."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.macro.enums import MacroIndicatorType


class MacroIndicator(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    value: float
    unit: Optional[str] = None
    indicator_type: MacroIndicatorType = MacroIndicatorType.OTHER
    recorded_at: Optional[datetime] = None


class MacroCache(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[int] = None
    indicators: list[MacroIndicator] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "MacroCache":
        raw = row.get("data") or row.get("indicators") or row
        indicators = []
        if isinstance(raw, dict):
            for key, value in raw.items():
                if isinstance(value, (int, float)):
                    indicators.append(
                        MacroIndicator(name=key, value=float(value))
                    )
        return cls(
            id=row.get("id"),
            indicators=indicators,
            raw_data=row,
            updated_at=row.get("updated_at"),
        )
