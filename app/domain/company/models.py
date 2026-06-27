"""Company domain models."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.company.enums import Exchange, Sector


class CompanyMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    eps: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None


class CompanyProfile(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    name: str
    sector: Sector = Sector.OTHER
    exchange: Exchange = Exchange.PSX
    description: Optional[str] = None
    metrics: CompanyMetrics = Field(default_factory=CompanyMetrics)
    updated_at: Optional[datetime] = None

    @classmethod
    def from_provider_row(cls, ticker: str, raw: dict[str, Any]) -> "CompanyProfile":
        return cls(
            ticker=ticker.upper(),
            name=raw.get("name") or raw.get("companyName") or ticker.upper(),
            sector=Sector.OTHER,
            description=raw.get("description"),
            metrics=CompanyMetrics(
                market_cap=raw.get("market_cap") or raw.get("mktCap"),
                pe_ratio=raw.get("pe_ratio") or raw.get("pe"),
                eps=raw.get("eps"),
                dividend_yield=raw.get("dividend_yield") or raw.get("dividendYield"),
            ),
        )
