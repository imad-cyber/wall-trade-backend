"""Map Capital Stake (csapis) API responses to contract schemas."""
from datetime import datetime, timezone
from typing import Any, Optional

from app.api.v1.schemas.company import (
    CompanyOverviewResponse,
    CompanyProfileResponse,
    PreMarketSchema,
    PriceRangeSchema,
    ScorecardSchema,
    StockDataSchema,
    StockRangesSchema,
)


def _first(raw: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_change_percent(value: Any) -> float:
    pct = _to_float(value)
    if abs(pct) <= 1 and pct != 0:
        return round(pct * 100, 4)
    return round(pct, 4)


def _normalize_status(raw_status: Any) -> str:
    if not raw_status:
        return "Closed"
    status = str(raw_status).strip().lower()
    mapping = {
        "open": "Open",
        "closed": "Closed",
        "pre-market": "Pre-Market",
        "premarket": "Pre-Market",
        "pre_market": "Pre-Market",
        "after-hours": "After-Hours",
        "afterhours": "After-Hours",
        "after_hours": "After-Hours",
    }
    return mapping.get(status, "Closed")


def _iso_timestamp(raw: Any) -> str:
    if isinstance(raw, str) and raw:
        return raw
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_ranges(quote: dict[str, Any], price: float) -> StockRangesSchema:
    day_low = _to_float(_first(quote, "low", "dayLow", "day_low"), price)
    day_high = _to_float(_first(quote, "high", "dayHigh", "day_high"), price)
    week_low = _to_float(_first(quote, "fiftyTwoWeekLow", "week52Low", "week_52_low", "low52"), day_low)
    week_high = _to_float(_first(quote, "fiftyTwoWeekHigh", "week52High", "week_52_high", "high52"), day_high)

    return StockRangesSchema(
        fair_value=None,
        day_range=PriceRangeSchema(low=day_low, high=day_high, current=price),
        week_52=PriceRangeSchema(low=week_low, high=week_high, current=price),
    )


def map_quote_to_stock_data(ticker: str, quote: dict[str, Any], profile: Optional[dict[str, Any]] = None) -> StockDataSchema:
    profile = profile or {}
    price = _to_float(_first(quote, "lastPrice", "last_price", "price", "close", "ltp"), 0.0)
    change = _to_float(_first(quote, "change", "netChange", "net_change"), 0.0)
    change_percent = _normalize_change_percent(
        _first(quote, "changePercent", "change_percent", "pctChange", "pct_change")
    )

    pre_market_raw = _first(quote, "preMarket", "pre_market")
    pre_market = None
    if isinstance(pre_market_raw, dict):
        pre_market = PreMarketSchema(
            price=_to_float(_first(pre_market_raw, "price", "lastPrice"), price),
            change=_to_float(_first(pre_market_raw, "change"), 0.0),
            change_percent=_normalize_change_percent(_first(pre_market_raw, "changePercent", "change_percent")),
            time=str(_first(pre_market_raw, "time", "timestamp", default="")),
        )

    name = (
        _first(quote, "name", "symbolName", "symbol_name", "companyName", "company_name")
        or _first(profile, "name", "companyName", "company_name", "symbolName")
        or ticker
    )

    return StockDataSchema(
        ticker=ticker.upper(),
        name=str(name),
        exchange=str(_first(quote, "exchange", "market", default="PSX") or "PSX"),
        currency=str(_first(quote, "currency", default="PKR") or "PKR"),
        price=price,
        change=change,
        change_percent=change_percent,
        status=_normalize_status(_first(quote, "status", "marketStatus", "market_status")),  # type: ignore[arg-type]
        last_updated=_iso_timestamp(_first(quote, "lastUpdated", "last_updated", "timestamp", "date")),
        pre_market=pre_market,
        ranges=_build_ranges(quote, price),
    )


def map_overview(
    ticker: str,
    quote: dict[str, Any],
    profile: Optional[dict[str, Any]] = None,
) -> CompanyOverviewResponse:
    stock = map_quote_to_stock_data(ticker, quote, profile)
    fair_value = None
    upside = None
    verdict = None

    data = stock.model_dump()
    data["scorecard"] = ScorecardSchema(
        fair_value=fair_value,
        fair_value_upside_percent=upside,
        verdict=verdict,
        risk_label="Moderate",
    )
    return CompanyOverviewResponse(**data)


def map_profile_basic(ticker: str, raw: dict[str, Any]) -> CompanyProfileResponse:
    return CompanyProfileResponse(
        ticker=ticker.upper(),
        description=_first(raw, "description", "businessSummary", "business_summary"),
        industry=_first(raw, "industry", "industryName", "industry_name"),
        sector=_first(raw, "sector", "sectorName", "sector_name"),
        employees=str(_first(raw, "employees", "fullTimeEmployees", "full_time_employees", default="")) or None,
        market=str(_first(raw, "market", "exchange", default="PSX") or "PSX"),
        website=_first(raw, "website", "webSite", "web_site"),
        founded_year=_first(raw, "foundedYear", "founded_year", "yearFounded"),
        headquarters=_first(raw, "headquarters", "address", "city"),
        ceo=_first(raw, "ceo", "ceoName", "ceo_name"),
    )


class CompanyMapper:
    """Legacy mapper — delegates to domain model factory."""

    @staticmethod
    def to_domain(ticker: str, raw: dict[str, Any]):
        from app.domain.company.models import CompanyProfile

        return CompanyProfile.from_provider_row(ticker, raw)
