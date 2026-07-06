from app.providers.capital_stake.v3_paths import financial_statement_path, lookback_days_for_range


def test_financial_statement_path_mapping():
    assert financial_statement_path("income", "annual") == "/company/financials/income/annual"
    assert financial_statement_path("balance-sheet", "quarterly") == "/company/financials/balance/quarterly"
    assert financial_statement_path("cash-flow", "annual") == "/company/financials/cashflow/annual"


def test_lookback_days_for_range():
    assert lookback_days_for_range("2y") == 800
    assert lookback_days_for_range("unknown", default=30) == 30
