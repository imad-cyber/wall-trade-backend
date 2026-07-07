"""Capital Stake API v3 path helpers."""

# csapis path variants — subscription/plan may expose only a subset.
TICKER_LIST_PATHS: tuple[str, ...] = (
    "/market/indices",
    "/market/tickers",
    "/indices",
    "/tickers",
)

STATEMENT_API_SLUG = {
    "income": "income",
    "balance-sheet": "balance",
    "balance": "balance",
    "cash-flow": "cashflow",
    "cashflow": "cashflow",
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
    slug = STATEMENT_API_SLUG.get(statement_type, statement_type)
    if period not in ("annual", "quarterly"):
        raise ValueError(f"Unsupported financial period: {period}")
    return f"/company/financials/{slug}/{period}"


def lookback_days_for_range(range_: str, default: int = 30) -> int:
    return RANGE_LOOKBACK_DAYS.get(range_, default)
