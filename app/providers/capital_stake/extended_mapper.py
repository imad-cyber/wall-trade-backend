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
    OwnershipBreakdownItem,
    OwnershipResponse,
    OwnershipTotal,
    PeriodReturnItem,
    PeriodReturnsResponse,
    StatColumn,
    StatItem,
    TopHolder,
)
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
        for key in ("data", "result", "rows", "points", "history", "items"):
            val = raw.get(key)
            if isinstance(val, list):
                return [r for r in val if isinstance(r, dict)]
    return []


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
        date = str(_first(row, "date", "Date", "timestamp", default=""))[:10]
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


def _map_index_row(row: dict[str, Any]) -> MarketSummaryIndex:
    symbol = str(_first(row, "symbol", "ticker", "code", default="")).upper()
    name = str(_first(row, "name", "indexName", "index_name", "title", default=symbol or "Index"))
    price = _to_float(_first(row, "lastPrice", "last_price", "price", "close", "value"), 0.0)
    change_percent = _normalize_change_percent(
        _first(row, "changePercent", "change_percent", "pctChange", "pct_change", "change")
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


def map_market_summary(
    indices_raw: list[dict[str, Any]],
    chart_points: list[OHLCVPoint],
    market_status: str = "Closed",
) -> MarketSummaryResponse:
    indices = [_map_index_row(row) for row in indices_raw if isinstance(row, dict)]
    featured = _pick_featured_index(indices)
    if featured is None:
        featured = MarketSummaryIndex(
            name="KSE-100",
            symbol="KSE100",
            price=0.0,
            currency="PKR",
            change_percent=0.0,
        )

    major = [idx for idx in indices if idx.symbol != featured.symbol][:6]
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
        {"label": "Prev. Close", "value": str(_first(q, "previousClose", "prevClose", default=price)), "locked": False},
        {"label": "Open", "value": str(_first(q, "open", default="—")), "locked": False},
        {"label": "Day's Range", "value": f"{_first(q, 'low', default='—')} - {_first(q, 'high', default='—')}", "locked": False},
        {"label": "52 wk Range", "value": f"{_first(q, 'fiftyTwoWeekLow', default='—')} - {_first(q, 'fiftyTwoWeekHigh', default='—')}", "locked": False},
        {"label": "Volume", "value": _fmt_large(_first(q, "volume")), "locked": False},
        {"label": "Market Cap", "value": _fmt_large(_first(m, "marketCap", "market_cap")), "locked": False},
        {"label": "Fair Value", "value": None, "locked": True, "pro": True},
        {"label": "Fair Value Upside", "value": None, "locked": True, "pro": True},
    ]
    fundamental_items = [
        {"label": "Revenue", "value": _fmt_large(_first(m, "revenue")), "locked": False},
        {"label": "Net Income", "value": _fmt_large(_first(m, "netIncome", "net_income")), "locked": False},
        {"label": "EPS", "value": str(_first(m, "eps", default="—")), "locked": False},
        {"label": "EPS Growth Forecast", "value": None, "locked": True, "pro": True},
        {"label": "P/E Ratio", "value": f"{_first(m, 'peRatio', 'pe_ratio', default='—')}x", "locked": False},
        {"label": "Dividend (Yield)", "value": str(_first(m, "dividendYield", default="—")), "locked": False},
    ]
    ratio_items = [
        {"label": "Return on Assets", "value": f"{_to_float(_first(m, 'returnOnAssets')):.1f}%", "locked": False},
        {"label": "Return on Equity", "value": f"{_to_float(_first(m, 'returnOnEquity')):.1f}%", "locked": False},
        {"label": "Beta", "value": str(_first(m, "beta", default="—")), "locked": False},
    ]

    columns = [
        StatColumn(group="Trading", items=[StatItem(**i) for i in apply_pro_lock(trading_items, tier=tier)]),
        StatColumn(group="Fundamentals", items=[StatItem(**i) for i in apply_pro_lock(fundamental_items, tier=tier)]),
        StatColumn(group="Ratios", items=[StatItem(**i) for i in apply_pro_lock(ratio_items, tier=tier)]),
    ]
    return CompanyStatisticsResponse(ticker=ticker.upper(), columns=columns)


def map_earnings(ticker: str, raw: dict[str, Any]) -> EarningsResponse:
    rows = _rows_from_list(raw)
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
    summary = EarningsSummary(
        latest_release=str(_first(latest, "date", "period", default=""))[:10] or None,
        eps=_to_float(_first(latest, "eps")) or None,
        eps_forecast=_to_float(_first(latest, "epsForecast", "eps_forecast")) or None,
        revenue=_to_float(_first(latest, "revenue")) or None,
        revenue_forecast=_to_float(_first(latest, "revenueForecast", "revenue_forecast")) or None,
        next_earnings_date=str(_first(raw, "nextEarningsDate", "next_earnings_date", default=""))[:10] or None,
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
            date=str(_first(r, "date", "exDate", default=""))[:10],
            amount=_to_float(_first(r, "amount", "dividend")),
            type=str(_first(r, "type", default="regular")),
        )
        for r in rows[:20]
    ]
    return DividendResponse(
        ticker=ticker.upper(),
        payout_ratio=_to_float(_first(raw, "payoutRatio", "payout_ratio")) or None,
        dividend_yield=str(_first(raw, "dividendYield", "dividend_yield", default="")) or None,
        annualized_payout=str(_first(raw, "annualizedPayout", default="")) or None,
        payout_frequency=str(_first(raw, "frequency", default="quarterly")) or None,
        history=history,
    )


def map_ownership(ticker: str, raw: dict[str, Any]) -> OwnershipResponse:
    breakdown_raw = _rows_from_list(_first(raw, "breakdown", default=raw))
    holders_raw = _rows_from_list(_first(raw, "topHolders", "top_holders", default=[]))
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
    total_raw = _first(raw, "total", default={}) or {}
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
    rows_raw = _rows_from_list(raw)
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
