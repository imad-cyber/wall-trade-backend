"""Capital Stake API response schemas."""
from typing import Any, Optional

from pydantic import BaseModel


class CapitalStakeCompanyResponse(BaseModel):
    name: Optional[str] = None
    companyName: Optional[str] = None
    description: Optional[str] = None
    market_cap: Optional[Any] = None
    mktCap: Optional[Any] = None
    pe_ratio: Optional[Any] = None
    pe: Optional[Any] = None
    eps: Optional[Any] = None
    dividend_yield: Optional[Any] = None
    dividendYield: Optional[Any] = None
