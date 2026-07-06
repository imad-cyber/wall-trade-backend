"""Financial statement response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FinancialStatementRow(BaseModel):
    period: str
    period_label: str
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capex: Optional[float] = None


class FinancialStatementResponse(BaseModel):
    ticker: str
    statement_type: Literal["income", "balance-sheet", "cash-flow"]
    period: Literal["annual", "quarterly"] = "annual"
    currency: str = "PKR"
    unit: str = "billions"
    rows: list[FinancialStatementRow] = Field(default_factory=list)
