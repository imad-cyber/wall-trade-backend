"""Capital Stake API v3 path helpers."""

# Ticker list path variants tried in order; first successful non-empty response wins.
# /market/tickers — subscribed (#1 All Tickers) but returns 404 on UAT; kept first for prod.
# /market/stocks  — subscribed (#3 All Symbols Overview); confirmed 200 on UAT.
# /market/indices — subscribed (#6 Indices Overview); confirmed 200 on UAT.
TICKER_LIST_PATHS: tuple[str, ...] = (
    "/market/tickers",
    "/market/stocks",
    "/market/indices",
)

# Key-metrics endpoints — subscribed (#14 annual, #15 quarterly).
# Income/balance/cashflow statements are not in the subscribed plan;
# key-metrics is the closest available data source.
KEY_METRICS_PATHS: dict[str, str] = {
    "annual": "/company/fundamentals/key-metrics/annual",
    "quarterly": "/company/fundamentals/key-metrics/quarterly",
}

RANGE_LOOKBACK_DAYS = {
    "1d": 5,
    "5d": 10,
    "1mo": 35,
    "3mo": 100,
    "6mo": 200,
    "1y": 400,
    "2y": 800,
    "5y": 2000,
    "max": 3650,
}


def financial_statement_path(statement_type: str, period: str) -> str:
    """Return the subscribed csapis path for financial/key-metrics data."""
    if period not in ("annual", "quarterly"):
        raise ValueError(f"Unsupported financial period: {period}")
    return KEY_METRICS_PATHS[period]


def lookback_days_for_range(range_: str, default: int = 30) -> int:
    return RANGE_LOOKBACK_DAYS.get(range_, default)
