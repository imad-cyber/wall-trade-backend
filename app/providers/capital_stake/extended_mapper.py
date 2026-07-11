"""Extended mappers for Capital Stake → contract schemas."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.api.v1.schemas.analysis import (
    AnalystConsensus,
    AnalystRating,
    AnalystResponse,
    EarningsCallResponse,
    SwotItem,
    SwotResponse,
    TechnicalAnalysisResponse,
    TechnicalTimeframe,
)
from app.api.v1.schemas.company import (
    CompanyStatisticsResponse,
    DividendHistoryItem,
    DividendResponse,
    EarningsChartPoint,
    EarningsResponse,
    EarningsSummary,
    FaqItem,
    FaqResponse,
    IndexComponentItem,
    OwnershipBreakdownItem,
    OwnershipResponse,
    OwnershipTotal,
    PeriodReturnItem,
    PeriodReturnsResponse,
    StatColumn,
    StatItem,
    TopHolder,
)
from app.api.v1.schemas.historical import HistoricalDataResponse, HistoricalRow
from app.api.v1.schemas.financials import FinancialStatementResponse, FinancialStatementRow
from app.api.v1.schemas.market import (
    MarketSummaryChartPoint,
    MarketSummaryIndex,
    MarketSummaryResponse,
    OHLCVPoint,
    OHLCVResponse,
    OpexDatesResponse,
    PeerMetric,
    PeerMetricPositions,
    PeersComparisonResponse,
    RelatedTickerItem,
    RelatedTickersResponse,
)
from app.api.v1.schemas.news import NewsArticle, NewsResponse, NewsThumbnail
from app.providers.capital_stake.mapper import _first, _iso_timestamp, _normalize_change_percent, _to_float, map_quote_to_stock_data

VALID_RANGES = frozenset({"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"})
VALID_INTERVALS = frozenset({"1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"})


def validate_ohlcv_params(range_: str, interval: str) -> None:
    from app.core.exceptions import ValidationError

    if range_ not in VALID_RANGES:
        raise ValidationError(f"Invalid range: {range_}", error_code="VALIDATION_ERROR")
    if interval not in VALID_INTERVALS:
        raise ValidationError(f"Invalid interval: {interval}", error_code="VALIDATION_ERROR")
    long_ranges = {"3mo", "6mo", "1y", "2y", "5y", "max"}
    if range_ in long_ranges and interval in {"1m", "5m", "15m", "30m", "1h"}:
        raise ValidationError(
            f"Interval {interval} not valid for range {range_}",
            error_code="VALIDATION_ERROR",
        )


def _rows_from_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        for key in ("data", "result", "rows", "points", "history", "items", "articles", "news"):
            val = raw.get(key)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
    return []


def _is_key_metrics_pivot(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    sample = rows[: min(3, len(rows))]
    return all(
        isinstance(row, dict) and "name" in row and "period" in row and "value" in row
        for row in sample
    )


# Capital Stake key-metrics `name` → internal field (substring match, case-insensitive).
# Names confirmed via https://capitalstake.com/docs/.../key-metrics
NAME_TO_FIELD: dict[str, str] = {
    "sales": "revenue",
    "earnings per share": "eps",
    "profit after taxation": "net_income",
    "dividend per share": "dividend_per_share",
    "cash payout ratio": "payout_ratio",
    "payout ratio": "payout_ratio",
    "book value per share": "book_value_per_share",
    "price earnings ratio": "pe_ratio",
    "price to earnings": "pe_ratio",
    "price/book ratio": "pb_ratio",
    "price to book": "pb_ratio",
    "long term debt to equity": "debt_to_equity",
    "debt to equity": "debt_to_equity",
    "current ratio": "current_ratio",
    "gross profit margin": "gross_margin",
    "dividend yield": "dividend_yield",
    "net profit margin": "net_profit_margin",
    "return on equity": "roe",
    "return on assets": "roa",
    "operating cash flow": "operating_cash_flow",
    "capital expenditure": "capex",
    "free cash flow": "free_cash_flow",
}


def _normalize_key_metrics_raw(raw: Any) -> list[dict[str, Any]]:
    """Normalize Capital Stake key-metrics into `{name, period, value}` pivot rows."""
    if isinstance(raw, list):
        if _is_key_metrics_pivot(raw):
            return [row for row in raw if isinstance(row, dict)]
        return [row for row in raw if isinstance(row, dict)]
    if isinstance(raw, dict):
        periods = raw.get("periods")
        fundamentals = raw.get("fundementals") or raw.get("fundamentals")
        if isinstance(periods, list) and isinstance(fundamentals, list):
            rows: list[dict[str, Any]] = []
            for metric in fundamentals:
                if not isinstance(metric, dict):
                    continue
                name = str(metric.get("name", ""))
                values = metric.get("values") or []
                for idx, period in enumerate(periods):
                    if idx < len(values):
                        rows.append(
                            {"name": name, "period": str(period), "value": values[idx]}
                        )
            return rows
    return []


def _extract_key_metric(
    rows: list[dict[str, Any]] | Any,
    name_pattern: str,
    default: Any = None,
    *,
    skip_ttm: bool = True,
) -> Any:
    """Extract the most recent non-TTM value for a named metric from key-metrics data."""
    pivot_rows = _normalize_key_metrics_raw(rows) if not (
        isinstance(rows, list) and rows and _is_key_metrics_pivot(rows)
    ) else rows
    pattern = name_pattern.lower()
    for row in pivot_rows:
        if not isinstance(row, dict):
            continue
        if pattern not in str(row.get("name", "")).lower():
            continue
        period = str(row.get("period", "")).upper()
        if skip_ttm and period == "TTM":
            continue
        return row.get("value", default)
    return default


def _period_sort_key(period: str) -> tuple[int, int]:
    parts = period.strip().split()
    if len(parts) == 2 and parts[0].startswith("Q"):
        try:
            return (int(parts[1]), int(parts[0][1:]))
        except ValueError:
            pass
    if parts and parts[0].isdigit():
        return (int(parts[0]), 0)
    return (0, 0)


def _rows_from_key_metrics_pivot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pivot Capital Stake key-metrics rows `{name, period, value}` into period records."""
    pivot_rows = _normalize_key_metrics_raw(rows) if not _is_key_metrics_pivot(rows) else rows
    by_period: dict[str, dict[str, Any]] = {}
    # Longer patterns first to avoid partial substring collisions.
    patterns = sorted(NAME_TO_FIELD.items(), key=lambda item: len(item[0]), reverse=True)
    for row in pivot_rows:
        period = str(row.get("period", "")).strip()
        if not period or period.upper() == "TTM":
            continue
        name_lower = str(row.get("name", "")).lower().strip()
        value = row.get("value")
        slot = by_period.setdefault(
            period,
            {"period": period, "period_label": period},
        )
        for pattern, field in patterns:
            if pattern in name_lower:
                slot[field] = value
                break
    return sorted(
        by_period.values(),
        key=lambda item: _period_sort_key(str(item.get("period", ""))),
        reverse=True,
    )


def _map_v3_market_state(state: str) -> str:
    mapping = {
        "OPN": "Open",
        "PRE": "Pre-Market",
        "RED": "Pre-Market",
        "PCL": "After-Hours",
        "BRK": "Closed",
        "HLT": "Closed",
        "CBR": "Closed",
        "SUS": "Closed",
    }
    return mapping.get(str(state).strip().upper(), "Closed")


def map_ohlcv(ticker: str, raw: dict[str, Any], range_: str, interval: str) -> OHLCVResponse:
    rows = _rows_from_list(raw)
    points: list[OHLCVPoint] = []
    highs: list[float] = []
    lows: list[float] = []

    for row in rows:
        close = _to_float(_first(row, "close", "Close", "adjClose", "lastPrice"), 0.0)
        if close == 0:
            continue
        high = _to_float(_first(row, "high", "High"), close)
        low = _to_float(_first(row, "low", "Low"), close)
        open_ = _to_float(_first(row, "open", "Open"), close)
        volume = int(_to_float(_first(row, "volume", "Volume"), 0))
        raw_date = _first(row, "date", "Date", "timestamp", "time", default="")
        if isinstance(raw_date, (int, float)):
            date = datetime.fromtimestamp(raw_date, tz=timezone.utc).strftime("%Y-%m-%d")
        else:
            date = str(raw_date)[:10]
        points.append(OHLCVPoint(date=date, open=open_, high=high, low=low, close=close, volume=volume))
        highs.append(high)
        lows.append(low)

    return OHLCVResponse(
        ticker=ticker.upper(),
        range=range_,
        interval=interval,
        fifty_two_week_high=max(highs) if highs else None,
        fifty_two_week_low=min(lows) if lows else None,
        points=points,
    )


FEATURED_INDEX_SYMBOLS = frozenset({"KSE100", "KSE-100", "KSE_100"})
_PSX_INDEX_PRIORITY = (
    "KSE30",
    "KSEALL",
    "ALLSHR",
    "KMI30",
    "MZNPI",
    "BKTI",
    "OGPTI",
    "PSXDIV20",
    "NITPGI",
    "MII30",
)


def _normalize_index_code(symbol: str) -> str:
    return symbol.upper().replace("-", "").replace("_", "")


def _map_index_row(row: dict[str, Any]) -> MarketSummaryIndex:
    symbol = str(_first(row, "code", "symbol", "ticker", "s", default="")).upper()
    name = str(_first(row, "name", "indexName", "index_name", "title", default=symbol or "Index"))
    if not name.strip():
        name = symbol or "Index"
    price = _to_float(
        _first(row, "lastPrice", "last_price", "price", "close", "value", "c", "ldcp", "ldci"),
        0.0,
    )
    change_percent = _normalize_change_percent(
        _first(row, "changePercent", "change_percent", "pctChange", "pct_change", "pch", "change")
    )
    currency = str(_first(row, "currency", default="PKR"))
    is_delayed = bool(_first(row, "delayed", "isDelayed", "is_delayed", default=False))
    return MarketSummaryIndex(
        name=name,
        symbol=symbol,
        price=price,
        currency=currency,
        change_percent=change_percent,
        is_delayed=is_delayed,
    )


def _pick_featured_index(indices: list[MarketSummaryIndex]) -> MarketSummaryIndex | None:
    for idx in indices:
        normalized = idx.symbol.replace("-", "").replace("_", "")
        if normalized in {"KSE100"} or "KSE100" in normalized:
            return idx
    return indices[0] if indices else None


def _major_index_sort_key(idx: MarketSummaryIndex) -> tuple[int, int | str]:
    code = _normalize_index_code(idx.symbol)
    for i, priority in enumerate(_PSX_INDEX_PRIORITY):
        if code == priority or code.startswith(priority):
            return (0, i)
    return (1, code)


def map_market_summary(
    indices_raw: list[dict[str, Any]],
    chart_points: list[OHLCVPoint],
    market_status: str = "Closed",
    featured_raw: dict[str, Any] | None = None,
) -> MarketSummaryResponse:
    indices = [_map_index_row(row) for row in indices_raw if isinstance(row, dict)]
    if featured_raw and isinstance(featured_raw, dict):
        featured = _map_index_row(featured_raw)
        if not featured.name.strip():
            featured = featured.model_copy(update={"name": "KSE-100"})
        if not featured.symbol:
            featured = featured.model_copy(update={"symbol": "KSE100"})
    else:
        featured = _pick_featured_index(indices)
    if featured is None:
        featured = MarketSummaryIndex(
            name="KSE-100",
            symbol="KSE100",
            price=0.0,
            currency="PKR",
            change_percent=0.0,
        )

    featured_code = _normalize_index_code(featured.symbol)
    major = sorted(
        [
            idx
            for idx in indices
            if _normalize_index_code(idx.symbol) != featured_code and idx.price > 0
        ],
        key=_major_index_sort_key,
    )[:6]
    chart_data = [
        MarketSummaryChartPoint(
            time=point.date[-5:] if len(point.date) >= 5 else point.date,
            value=point.close,
        )
        for point in chart_points[-12:]
    ]

    return MarketSummaryResponse(
        featured_index=featured,
        chart_data=chart_data,
        major_indices=major,
        market_status=market_status,
        last_updated=_iso_timestamp(None),
    )


def map_peers(ticker: str, sector: str, peer_tickers: list[str], metrics_raw: list[dict]) -> PeersComparisonResponse:
    metrics: list[PeerMetric] = []
    for row in metrics_raw:
        metrics.append(
            PeerMetric(
                metric=str(_first(row, "metric", "name", default="Metric")),
                subject=str(_first(row, "subject", "value", default="—")),
                peers=str(_first(row, "peers", default="—")),
                sector=str(_first(row, "sector", default="—")),
                positions=PeerMetricPositions(
                    sector=int(_to_float(_first(row, "sectorPosition", "sector_position"), 50)),
                    subject=int(_to_float(_first(row, "subjectPosition", "subject_position"), 50)),
                    peers=int(_to_float(_first(row, "peersPosition", "peers_position"), 50)),
                ),
            )
        )
    if not metrics:
        metrics = [
            PeerMetric(
                metric="P/E Ratio",
                subject="—",
                peers="—",
                sector="—",
                positions=PeerMetricPositions(),
            )
        ]
    return PeersComparisonResponse(ticker=ticker.upper(), sector=sector, peers=peer_tickers, metrics=metrics)


def map_related(ticker: str, items: list[dict[str, Any]]) -> RelatedTickersResponse:
    related: list[RelatedTickerItem] = []
    for item in items:
        related.append(
            RelatedTickerItem(
                name=str(_first(item, "name", "symbolName", default=item.get("ticker", ""))),
                ticker=str(_first(item, "ticker", "symbol", default="")).upper(),
                price=_to_float(_first(item, "price", "lastPrice"), 0),
                change_percent=_normalize_change_percent(_first(item, "changePercent", "change_percent")),
            )
        )
    return RelatedTickersResponse(ticker=ticker.upper(), related=related)


def compute_opex_dates(ticker: str, count: int = 6) -> OpexDatesResponse:
    """Compute 3rd-Friday opex dates for PSX (approximation)."""
    today = datetime.now(timezone.utc).date()
    dates: list[str] = []
    year, month = today.year, today.month
    while len(dates) < count:
        first = datetime(year, month, 1, tzinfo=timezone.utc)
        fridays = 0
        day = first
        while day.month == month:
            if day.weekday() == 4:
                fridays += 1
                if fridays == 3:
                    if day.date() >= today:
                        dates.append(day.strftime("%Y-%m-%d"))
                    break
            day += timedelta(days=1)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return OpexDatesResponse(ticker=ticker.upper(), opex_dates=dates)


def _fmt_large(value: Any) -> str:
    num = _to_float(value, 0)
    if num == 0:
        return "—"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.2f}T"
    if abs_num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    if abs_num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    return f"{num:.2f}"


def map_statistics(ticker: str, quote: dict, metrics: dict, *, tier: str) -> CompanyStatisticsResponse:
    from app.utils.tiering import apply_pro_lock

    q = quote or {}
    m = metrics or {}
    price = _to_float(_first(q, "lastPrice", "price"), 0)

    trading_items = [
        {"label": "Prev. Close", "value": str(_first(q, "previousClose", "prevClose", "ldcp", default=price)), "locked": False},
        {"label": "Open", "value": str(_first(q, "open", default="—")), "locked": False},
        {"label": "Day's Range", "value": f"{_first(q, 'lcap', 'low', default='—')} - {_first(q, 'ucap', 'high', default='—')}", "locked": False},
        {"label": "52 wk Range", "value": f"{_first(q, 'low52', 'fiftyTwoWeekLow', default='—')} - {_first(q, 'high52', 'fiftyTwoWeekHigh', default='—')}", "locked": False},
        {"label": "Volume", "value": _fmt_large(_first(q, "ldcv", "volume")), "locked": False},
        {"label": "Market Cap", "value": _fmt_large(_first(q, "market_cap", "marketCap")), "locked": False},
        {"label": "Shares Outstanding", "value": _fmt_large(_first(q, "shares")), "locked": False},
        {"label": "Free Float", "value": _fmt_large(_first(q, "free_float")), "locked": False},
        {"label": "Fair Value", "value": None, "locked": True, "pro": True},
        {"label": "Fair Value Upside", "value": None, "locked": True, "pro": True},
    ]
    fundamental_items = [
        {"label": "Revenue", "value": _fmt_large(_first(m, "revenue", "sales")), "locked": False},
        {"label": "Net Income", "value": _fmt_large(_first(m, "netIncome", "net_income", "pat")), "locked": False},
        {"label": "EPS", "value": str(_first(m, "eps", default="—")), "locked": False},
        {"label": "EPS Growth Forecast", "value": str(_first(m, "eps_growth", "epsGrowth", default="—")), "locked": False},
        {"label": "P/E Ratio", "value": f"{_first(m, 'peRatio', 'pe_ratio', 'pe_current', default='—')}x", "locked": False},
        {"label": "Dividend (Yield)", "value": str(_first(m, "dividendYield", "yield_estimate", default="—")), "locked": False},
    ]
    ratio_items = [
        {"label": "Return on Assets", "value": f"{_to_float(_first(m, 'returnOnAssets', 'roa')):.1f}%", "locked": False},
        {"label": "Return on Equity", "value": f"{_to_float(_first(m, 'returnOnEquity', 'roe')):.1f}%", "locked": False},
        {"label": "Book Value", "value": str(_first(m, "book_value", "book_value_per_share", default="—")), "locked": False},
        {"label": "Beta", "value": str(_first(m, "beta", default="—")), "locked": False},
    ]

    columns = [
        StatColumn(group="Trading", items=[StatItem(**i) for i in apply_pro_lock(trading_items, tier=tier)]),
        StatColumn(group="Fundamentals", items=[StatItem(**i) for i in apply_pro_lock(fundamental_items, tier=tier)]),
        StatColumn(group="Ratios", items=[StatItem(**i) for i in apply_pro_lock(ratio_items, tier=tier)]),
    ]
    return CompanyStatisticsResponse(ticker=ticker.upper(), columns=columns)


def _field_value_for_period(fields: list[dict[str, Any]], key: str, period_index: int) -> Any:
    for field in fields:
        if not isinstance(field, dict):
            continue
        field_key = str(field.get("key") or "").lower()
        label = str(field.get("label") or "").lower()
        if field_key == key.lower() or key.lower() in label:
            values = field.get("values") or []
            if period_index < len(values):
                return values[period_index]
    return None


def _period_label(period: dict[str, Any]) -> str:
    year = str(period.get("year") or "")
    quarter = str(period.get("quarter") or "")
    period_end = str(period.get("period_end") or "")
    if quarter:
        return f"{year} {quarter}".strip()
    if year:
        return year
    return period_end[:10]


def _financial_rows_from_v3(raw: dict[str, Any]) -> list[dict[str, Any]]:
    periods = raw.get("periods") if isinstance(raw.get("periods"), list) else []
    fields = raw.get("fields") if isinstance(raw.get("fields"), list) else []
    rows: list[dict[str, Any]] = []
    for idx, period in enumerate(periods):
        if not isinstance(period, dict):
            continue
        label = _period_label(period)
        rows.append(
            {
                "period": label,
                "period_label": label,
                "revenue": _field_value_for_period(fields, "sales", idx),
                "net_income": _field_value_for_period(fields, "pat", idx),
                "gross_profit": _field_value_for_period(fields, "gross_profit", idx),
                "operating_income": _field_value_for_period(fields, "op_profit", idx),
                "total_assets": _field_value_for_period(fields, "nc_assets", idx),
                "total_liabilities": _field_value_for_period(fields, "liabilities", idx),
                "total_equity": _field_value_for_period(fields, "equity", idx),
                "operating_cash_flow": _field_value_for_period(fields, "op_cash", idx),
                "investing_cash_flow": _field_value_for_period(fields, "inv_cash", idx),
                "financing_cash_flow": _field_value_for_period(fields, "fin_cash", idx),
                "free_cash_flow": _field_value_for_period(fields, "fcf", idx),
                "eps": _field_value_for_period(fields, "eps", idx),
            }
        )
    return rows


def map_earnings(ticker: str, raw: dict[str, Any]) -> EarningsResponse:
    if isinstance(raw, dict) and raw.get("fields"):
        rows = _financial_rows_from_v3(raw)
    else:
        pivot_rows = _normalize_key_metrics_raw(raw)
        if pivot_rows and _is_key_metrics_pivot(pivot_rows):
            rows = _rows_from_key_metrics_pivot(pivot_rows)
        else:
            list_rows = _rows_from_list(raw)
            rows = (
                _rows_from_key_metrics_pivot(list_rows)
                if _is_key_metrics_pivot(list_rows)
                else list_rows
            )
    chart: list[EarningsChartPoint] = []
    for row in rows[:8]:
        chart.append(
            EarningsChartPoint(
                period=str(_first(row, "period", "quarter", default="")),
                period_label=str(_first(row, "periodLabel", "period_label", default="")),
                revenue=_to_float(_first(row, "revenue")),
                revenue_forecast=_to_float(_first(row, "revenueForecast", "revenue_forecast")),
                eps=_to_float(_first(row, "eps")),
                eps_forecast=_to_float(_first(row, "epsForecast", "eps_forecast")),
            )
        )
    latest = rows[0] if rows else {}
    prior = rows[1] if len(rows) > 1 else {}
    summary = EarningsSummary(
        latest_release=str(_first(latest, "date", "period", default=""))[:10] or None,
        eps=_to_float(_first(latest, "eps")) or None,
        eps_forecast=_to_float(_first(latest, "epsForecast", "eps_forecast"))
        or (_to_float(_first(prior, "eps")) or None),
        revenue=_to_float(_first(latest, "revenue")) or None,
        revenue_forecast=_to_float(_first(latest, "revenueForecast", "revenue_forecast"))
        or (_to_float(_first(prior, "revenue")) or None),
        next_earnings_date=(
            str(_first(raw, "nextEarningsDate", "next_earnings_date", default=""))[:10]
            if isinstance(raw, dict)
            else None
        )
        or None,
    )
    if summary.eps and summary.eps_forecast:
        summary.eps_beat = summary.eps >= summary.eps_forecast
    if summary.revenue and summary.revenue_forecast:
        summary.revenue_beat = summary.revenue >= summary.revenue_forecast
    return EarningsResponse(ticker=ticker.upper(), summary=summary, chart=chart)


def map_dividends(ticker: str, raw: dict[str, Any]) -> DividendResponse:
    rows = _rows_from_list(raw)
    history = [
        DividendHistoryItem(
            date=str(_first(r, "date", "exDate", "ex_date", default=""))[:10],
            amount=_to_float(_first(r, "amount", "dividend", "dividend_amount")),
            type=str(_first(r, "type", "title", default="regular")),
        )
        for r in rows[:20]
    ]
    latest = rows[0] if rows else {}
    return DividendResponse(
        ticker=ticker.upper(),
        payout_ratio=_to_float(_first(raw, "payoutRatio", "payout_ratio")) or None,
        dividend_yield=str(_first(raw, "dividendYield", "dividend_yield", default="")) or None,
        annualized_payout=str(_first(raw, "annualizedPayout", "dividend", default=_first(latest, "dividend", default=""))) or None,
        payout_frequency=str(_first(raw, "frequency", default="annual")) or None,
        history=history,
    )


def map_ownership(ticker: str, raw: dict[str, Any]) -> OwnershipResponse:
    if isinstance(raw, dict) and raw.get("fields"):
        periods = raw.get("periods") if isinstance(raw.get("periods"), list) else []
        fields = raw.get("fields") if isinstance(raw.get("fields"), list) else []
        latest_idx = 0
        breakdown_raw: list[dict[str, Any]] = []
        for field in fields:
            if not isinstance(field, dict) or field.get("is_heading"):
                continue
            values = field.get("values") or []
            if not values:
                continue
            pct = values[latest_idx] if latest_idx < len(values) else values[0]
            breakdown_raw.append(
                {
                    "type": field.get("label"),
                    "percent": f"{_to_float(pct) * 100:.2f}%",
                    "shares": "—",
                    "value": "—",
                }
            )
        holders_raw: list[dict[str, Any]] = []
        total_raw = {"percent": "100.00%"}
    else:
        breakdown_raw = _rows_from_list(_first(raw, "breakdown", default=raw))
        holders_raw = _rows_from_list(_first(raw, "topHolders", "top_holders", default=[]))
        total_raw = _first(raw, "total", default={}) or {}
    breakdown = [
        OwnershipBreakdownItem(
            type=str(_first(b, "type", "category", default="Unknown")),
            color=str(_first(b, "color", default="#64748b")),
            shares=str(_first(b, "shares", default="—")),
            percent=str(_first(b, "percent", "percentage", default="—")),
            value=str(_first(b, "value", default="—")),
        )
        for b in breakdown_raw
    ]
    top_holders = [
        TopHolder(
            holder=str(_first(h, "holder", "name", default="Unknown")),
            percent=str(_first(h, "percent", "percentage", default="—")),
            shares=str(_first(h, "shares", default="—")),
            reported_date=str(_first(h, "reportedDate", "date", default=""))[:10],
            value=str(_first(h, "value", default="—")),
        )
        for h in holders_raw
    ]
    total_raw = total_raw if isinstance(total_raw, dict) else {}
    return OwnershipResponse(
        ticker=ticker.upper(),
        total=OwnershipTotal(
            shares=str(_first(total_raw, "shares", default="—")),
            percent=str(_first(total_raw, "percent", default="100.00%")),
            value=str(_first(total_raw, "value", default="—")),
        ),
        breakdown=breakdown,
        top_holders=top_holders,
    )


def map_historical(ticker: str, ohlcv: OHLCVResponse) -> HistoricalDataResponse:
    rows: list[HistoricalRow] = []
    points = sorted(ohlcv.points, key=lambda p: p.date, reverse=True)
    for i, point in enumerate(points):
        prev = points[i + 1] if i + 1 < len(points) else None
        change_pct = None
        if prev and prev.close:
            change_pct = round((point.close - prev.close) / prev.close * 100, 2)
        rows.append(
            HistoricalRow(
                date=point.date,
                open=point.open,
                high=point.high,
                low=point.low,
                close=point.close,
                volume=point.volume,
                change_percent=change_pct,
            )
        )
    return HistoricalDataResponse(
        ticker=ticker.upper(),
        range=ohlcv.range,
        interval=ohlcv.interval,
        rows=rows,
        total=len(rows),
    )


def map_index_component(code: str, raw: dict[str, Any]) -> IndexComponentItem:
    name = str(_first(raw, "name", "indexName", "index_name", "title", "code", default=code))
    last = _to_float(_first(raw, "lastPrice", "last_price", "close", "value", "c", "ldci", "ldcp"), 0)
    high = _to_float(_first(raw, "high", "dayHigh", "day_high")) or None
    low = _to_float(_first(raw, "low", "dayLow", "day_low")) or None
    change = _to_float(_first(raw, "change", "netChange")) or None
    change_pct = _normalize_change_percent(_first(raw, "changePercent", "change_percent", "pctChange", "pch")) or None
    time_ = str(_first(raw, "date", "timestamp", "time", default="")) or None
    return IndexComponentItem(
        index_code=code.upper(),
        index_name=name,
        last=last,
        high=high,
        low=low,
        change=change,
        change_percent=change_pct,
        time=time_,
    )


def compute_period_returns(ticker: str, points: list[OHLCVPoint]) -> PeriodReturnsResponse:
    if not points:
        return PeriodReturnsResponse(ticker=ticker.upper(), returns=[])

    closes = [(p.date, p.close) for p in points if p.close]
    if not closes:
        return PeriodReturnsResponse(ticker=ticker.upper(), returns=[])

    latest_price = closes[-1][1]
    labels = [("1 Day", 1), ("1 Week", 5), ("1 Month", 21), ("3 Months", 63), ("6 Months", 126), ("1 Year", 252), ("5 Years", 1260), ("Max", len(closes) - 1)]
    returns: list[PeriodReturnItem] = []
    for label, offset in labels:
        idx = max(0, len(closes) - 1 - offset)
        base = closes[idx][1]
        if base:
            pct = round((latest_price - base) / base * 100, 2)
        else:
            pct = 0.0
        returns.append(PeriodReturnItem(label=label, value=pct))
    return PeriodReturnsResponse(ticker=ticker.upper(), returns=returns)


def map_faq(ticker: str, stock_name: str, price: float, currency: str = "PKR") -> FaqResponse:
    now = _iso_timestamp(None)
    return FaqResponse(
        ticker=ticker.upper(),
        items=[
            FaqItem(
                question=f"What Is the {ticker.upper()} Stock Price Today?",
                answer=f"The {ticker.upper()} stock price today is {price:.2f} {currency}.",
                generated_at=now,
            ),
            FaqItem(
                question=f"What Is {stock_name}'s Market?",
                answer=f"{stock_name} ({ticker.upper()}) is listed on the Pakistan Stock Exchange (PSX).",
                generated_at=now,
            ),
        ],
    )


def map_financial_statement(
    ticker: str,
    raw: dict[str, Any],
    statement_type: str,
    period: str,
) -> FinancialStatementResponse:
    if isinstance(raw, dict) and raw.get("fields"):
        rows_raw = _financial_rows_from_v3(raw)
    else:
        pivot_rows = _normalize_key_metrics_raw(raw)
        rows_raw = (
            _rows_from_key_metrics_pivot(pivot_rows)
            if pivot_rows
            else _rows_from_list(raw)
        )
    rows: list[FinancialStatementRow] = []
    for row in rows_raw:
        rows.append(
            FinancialStatementRow(
                period=str(_first(row, "period", "year", "date", default="")),
                period_label=str(_first(row, "periodLabel", "period_label", default="")),
                revenue=_to_float(_first(row, "revenue")) or None,
                net_income=_to_float(_first(row, "netIncome", "net_income")) or None,
                gross_profit=_to_float(_first(row, "grossProfit", "gross_profit")) or None,
                operating_income=_to_float(_first(row, "operatingIncome", "operating_income")) or None,
                ebitda=_to_float(_first(row, "ebitda")) or None,
                total_assets=_to_float(_first(row, "totalAssets", "total_assets")) or None,
                total_liabilities=_to_float(_first(row, "totalLiabilities", "total_liabilities")) or None,
                total_equity=_to_float(_first(row, "totalEquity", "total_equity")) or None,
                cash_and_equivalents=_to_float(_first(row, "cashAndEquivalents", "cash")) or None,
                total_debt=_to_float(_first(row, "totalDebt", "total_debt")) or None,
                operating_cash_flow=_to_float(_first(row, "operatingCashFlow")) or None,
                investing_cash_flow=_to_float(_first(row, "investingCashFlow")) or None,
                financing_cash_flow=_to_float(_first(row, "financingCashFlow")) or None,
                free_cash_flow=_to_float(_first(row, "freeCashFlow")) or None,
                capex=_to_float(_first(row, "capex")) or None,
            )
        )
    return FinancialStatementResponse(
        ticker=ticker.upper(),
        statement_type=statement_type,  # type: ignore[arg-type]
        period=period,  # type: ignore[arg-type]
        rows=rows,
    )


def map_news(
    ticker: str,
    articles_raw: list[dict],
    *,
    category: str,
    page: int,
    page_size: int,
    tier: str,
) -> NewsResponse:
    categories = ["Recent", "Analysis", "Earnings", "Company", "Analyst Ratings", "Pro"]
    articles: list[NewsArticle] = []
    for idx, row in enumerate(articles_raw):
        is_pro = bool(_first(row, "isPro", "is_pro", default=False))
        headline = str(_first(row, "headline", "title", default=""))
        url = _first(row, "url", "link")
        if is_pro and tier == "free":
            url = None
            if len(headline) > 60:
                headline = headline[:60] + "…"
        articles.append(
            NewsArticle(
                id=str(_first(row, "id", default=f"{ticker}-{idx}")),
                headline=headline,
                source=str(_first(row, "source", "publisher", default="Unknown")),
                published_at=str(_first(row, "publishedAt", "published_at", "date", default="")),
                time_ago=str(_first(row, "timeAgo", "time_ago", default="")),
                is_pro=is_pro,
                category=str(_first(row, "category", default=category)),
                url=url,
                thumbnail=NewsThumbnail(
                    bg=str(_first(row, "thumbnailBg", default="#1e293b")),
                    label=ticker.upper(),
                ),
            )
        )
    start = (page - 1) * page_size
    page_articles = articles[start : start + page_size]
    return NewsResponse(
        ticker=ticker.upper(),
        active_category=category,
        categories=categories,
        articles=page_articles,
        total=len(articles),
        page=page,
        page_size=page_size,
    )


def map_analyst_from_consensus(ticker: str, consensus_raw: dict, price: float, page: int, limit: int) -> AnalystResponse:
    summary = consensus_raw.get("recommendation_summary") if isinstance(consensus_raw.get("recommendation_summary"), list) else []
    ratings_raw: list[dict[str, Any]] = []
    for row in summary:
        if not isinstance(row, dict):
            continue
        ratings_raw.append(
            {
                "firm": row.get("company"),
                "analyst": row.get("analyst"),
                "position": row.get("action"),
                "rating": row.get("action"),
                "price_target": row.get("target"),
                "date": row.get("date"),
                "action": row.get("action"),
            }
        )
    dist = (consensus_raw.get("consensus") or {}).get("rating_distribution") or {}
    if dist and not ratings_raw:
        ratings_raw = [
            {"position": "Buy", "rating": "Buy", "firm": "Consensus", "price_target": (consensus_raw.get("price_target") or {}).get("average")},
        ] * int(dist.get("buy") or 0)
        ratings_raw += [
            {"position": "Hold", "rating": "Hold", "firm": "Consensus", "price_target": (consensus_raw.get("price_target") or {}).get("average")},
        ] * int(dist.get("hold") or 0)
        ratings_raw += [
            {"position": "Sell", "rating": "Sell", "firm": "Consensus", "price_target": (consensus_raw.get("price_target") or {}).get("average")},
        ] * int(dist.get("sell") or 0)
    return map_analyst(ticker, ratings_raw, page, limit, price)


def map_analyst_from_targets(ticker: str, targets_raw: list[dict], price: float, page: int, limit: int) -> AnalystResponse:
    ratings_raw: list[dict[str, Any]] = []
    for row in targets_raw:
        if not isinstance(row, dict):
            continue
        ratings_raw.append(
            {
                "firm": row.get("sn") or row.get("sc"),
                "position": row.get("act") or row.get("pos"),
                "rating": row.get("act") or row.get("pos"),
                "price_target": row.get("tgt"),
                "date": row.get("mod") or row.get("crt"),
                "action": row.get("act"),
            }
        )
    return map_analyst(ticker, ratings_raw, page, limit, price)


def map_analyst(ticker: str, ratings_raw: list[dict], page: int, limit: int, price: float) -> AnalystResponse:
    ratings: list[AnalystRating] = []
    buy = hold = sell = 0
    for row in ratings_raw:
        position = str(_first(row, "position", "rating", default="Hold")).title()
        if position not in ("Buy", "Hold", "Sell"):
            position = "Hold"
        if position == "Buy":
            buy += 1
        elif position == "Sell":
            sell += 1
        else:
            hold += 1
        pt = _to_float(_first(row, "priceTarget", "price_target"))
        upside = round((pt - price) / price * 100, 2) if price and pt else None
        ratings.append(
            AnalystRating(
                firm=str(_first(row, "firm", "analyst", default="Unknown")),
                position=position,  # type: ignore[arg-type]
                price_target=pt or None,
                upside_percent=upside,
                action=str(_first(row, "action", default="Maintain")),
                date=str(_first(row, "date", default=""))[:10],
            )
        )
    total = len(ratings)
    buy_pct = buy / total * 100 if total else 0
    if buy_pct > 60:
        label = "Strong Buy"
    elif buy_pct > 40:
        label = "Buy"
    elif sell > buy:
        label = "Sell"
    else:
        label = "Hold"
    targets = [r.price_target for r in ratings if r.price_target]
    avg_target = sum(targets) / len(targets) if targets else None
    upside = round((avg_target - price) / price * 100, 2) if price and avg_target else None
    start = (page - 1) * limit
    return AnalystResponse(
        ticker=ticker.upper(),
        consensus=AnalystConsensus(total=total, buy=buy, hold=hold, sell=sell, label=label, price_target=avg_target, upside_percent=upside),
        ratings=ratings[start : start + limit],
        total_ratings=total,
        page=page,
        page_size=limit,
    )


def map_swot(ticker: str, items_raw: list[dict]) -> SwotResponse:
    items = [
        SwotItem(
            category=str(_first(r, "category", default="STRENGTH")).upper(),  # type: ignore[arg-type]
            label=str(_first(r, "label", "title", default="")),
            description=str(_first(r, "description", "text", default="")),
            icon=str(_first(r, "icon", default="shield")),
        )
        for r in items_raw
    ]
    return SwotResponse(ticker=ticker.upper(), generated_at=_iso_timestamp(None), items=items)


def map_technical(ticker: str, raw: dict, *, tier: str) -> TechnicalAnalysisResponse:
    locked_short = tier == "free"
    indicators = raw.get("indicators") if isinstance(raw.get("indicators"), list) else []
    if indicators:
        overall = "Neutral"
        for indicator in indicators:
            name = str(indicator.get("name", "")).lower()
            values = indicator.get("values") or []
            if name == "rsi" and values:
                rsi = _to_float(values[0], 50)
                overall = "Bullish" if rsi >= 55 else "Bearish" if rsi <= 45 else "Neutral"
                break
        return TechnicalAnalysisResponse(
            ticker=ticker.upper(),
            snapshot_at=_iso_timestamp(None),
            overall_signal=overall,
            timeframes=[
                TechnicalTimeframe(
                    id="1d",
                    label="Daily",
                    signal=overall,
                    signal_type="neutral",
                    locked=False,
                )
            ],
        )
    timeframes_def = [
        ("1m", "1 Min", locked_short),
        ("5m", "5 Min", locked_short),
        ("15m", "15 Min", locked_short),
        ("30m", "30 Min", False),
        ("1h", "Hourly", False),
        ("5h", "5 Hours", False),
        ("1d", "Daily", False),
        ("1w", "Weekly", False),
        ("1mo", "Monthly", False),
    ]
    raw_tf = {str(_first(r, "id", "timeframe")): r for r in _rows_from_list(raw)}
    timeframes: list[TechnicalTimeframe] = []
    for tf_id, label, locked in timeframes_def:
        row = raw_tf.get(tf_id, {})
        signal = None if locked else str(_first(row, "signal", default="Neutral"))
        signal_type = None if locked else _first(row, "signalType", "signal_type")
        timeframes.append(
            TechnicalTimeframe(
                id=tf_id,
                label=label,
                signal=signal,
                signal_type=signal_type,  # type: ignore[arg-type]
                locked=locked,
            )
        )
    return TechnicalAnalysisResponse(
        ticker=ticker.upper(),
        snapshot_at=_iso_timestamp(None),
        overall_signal=str(_first(raw, "overallSignal", "overall_signal", default="Neutral")),
        timeframes=timeframes,
    )


def map_earnings_call(ticker: str, raw: dict) -> EarningsCallResponse:
    bullets = _first(raw, "bullets", "summary", default=[])
    if isinstance(bullets, str):
        bullets = [bullets]
    return EarningsCallResponse(
        ticker=ticker.upper(),
        quarter=str(_first(raw, "quarter", default="")),
        call_date=str(_first(raw, "callDate", "call_date", default=""))[:10],
        last_updated=_iso_timestamp(_first(raw, "lastUpdated", "last_updated")),
        bullets=list(bullets) if isinstance(bullets, list) else [],
    )
