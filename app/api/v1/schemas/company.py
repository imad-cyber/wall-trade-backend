"""Contract response schemas for company endpoints."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class PriceRangeSchema(BaseModel):
    low: float
    high: float
    current: float


class StockRangesSchema(BaseModel):
    fair_value: Optional[PriceRangeSchema] = None
    day_range: PriceRangeSchema
    week_52: PriceRangeSchema


class PreMarketSchema(BaseModel):
    price: float
    change: float
    change_percent: float
    time: str


class ScorecardSchema(BaseModel):
    fair_value: Optional[float] = None
    fair_value_upside_percent: Optional[float] = None
    verdict: Optional[str] = None
    risk_label: Optional[str] = None


class StockDataSchema(BaseModel):
    ticker: str
    name: str
    exchange: str = "PSX"
    currency: str = "PKR"
    price: float
    change: float
    change_percent: float
    status: Literal["Open", "Closed", "Pre-Market", "After-Hours"] = "Closed"
    last_updated: str
    pre_market: Optional[PreMarketSchema] = None
    ranges: StockRangesSchema


class CompanyOverviewResponse(StockDataSchema):
    scorecard: ScorecardSchema = Field(default_factory=ScorecardSchema)


class CompanyExecutiveItem(BaseModel):
    name: str
    title: str
    since: Optional[str] = None


class CompanyProfileResponse(BaseModel):
    ticker: str
    description: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    employees: Optional[str] = None
    market: str = "PSX"
    website: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    ceo: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    executives: list[CompanyExecutiveItem] = Field(default_factory=list)


class StatItem(BaseModel):
    label: str
    value: Optional[str] = None
    locked: bool = False
    pro: bool = False


class StatColumn(BaseModel):
    group: str
    items: list[StatItem] = Field(default_factory=list)


class CompanyStatisticsResponse(BaseModel):
    ticker: str
    columns: list[StatColumn] = Field(default_factory=list)


class EarningsSummary(BaseModel):
    latest_release: Optional[str] = None
    eps: Optional[float] = None
    eps_forecast: Optional[float] = None
    eps_beat: Optional[bool] = None
    revenue: Optional[float] = None
    revenue_forecast: Optional[float] = None
    revenue_beat: Optional[bool] = None
    next_earnings_date: Optional[str] = None


class EarningsChartPoint(BaseModel):
    period: str
    period_label: str
    revenue: Optional[float] = None
    revenue_forecast: Optional[float] = None
    eps: Optional[float] = None
    eps_forecast: Optional[float] = None


class EarningsResponse(BaseModel):
    ticker: str
    summary: EarningsSummary = Field(default_factory=EarningsSummary)
    chart: list[EarningsChartPoint] = Field(default_factory=list)


class DividendHistoryItem(BaseModel):
    date: str
    amount: float
    type: str = "regular"


class DividendResponse(BaseModel):
    ticker: str
    payout_ratio: Optional[float] = None
    earnings_retained_percent: Optional[float] = None
    eps_note: Optional[str] = None
    dividend_yield: Optional[str] = None
    industry_median_yield: Optional[str] = None
    annualized_payout: Optional[str] = None
    payout_frequency: Optional[str] = None
    five_year_growth: Optional[str] = None
    history: list[DividendHistoryItem] = Field(default_factory=list)


class OwnershipTotal(BaseModel):
    shares: str = "—"
    percent: str = "100.00%"
    value: str = "—"


class OwnershipBreakdownItem(BaseModel):
    type: str
    color: str = "#64748b"
    shares: str = "—"
    percent: str = "—"
    value: str = "—"


class TopHolder(BaseModel):
    holder: str
    percent: str
    shares: str
    reported_date: str
    value: str


class OwnershipResponse(BaseModel):
    ticker: str
    total: OwnershipTotal = Field(default_factory=OwnershipTotal)
    breakdown: list[OwnershipBreakdownItem] = Field(default_factory=list)
    top_holders: list[TopHolder] = Field(default_factory=list)


class PeriodReturnItem(BaseModel):
    label: str
    value: float


class PeriodReturnsResponse(BaseModel):
    ticker: str
    returns: list[PeriodReturnItem] = Field(default_factory=list)


class FaqItem(BaseModel):
    question: str
    answer: str
    generated_at: str


class FaqResponse(BaseModel):
    ticker: str
    items: list[FaqItem] = Field(default_factory=list)


class IndexComponentItem(BaseModel):
    index_code: str
    index_name: str
    last: float = 0.0
    high: Optional[float] = None
    low: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    time: Optional[str] = None


class IndexComponentResponse(BaseModel):
    ticker: str
    components: list[IndexComponentItem] = Field(default_factory=list)
