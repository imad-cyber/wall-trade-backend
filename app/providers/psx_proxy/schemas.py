"""PSX Proxy response schemas."""
from typing import Any, Optional

from pydantic import BaseModel


class PSXPriceResponse(BaseModel):
    ticker: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[Any] = None
    last: Optional[Any] = None
    change: Optional[Any] = None
    change_percent: Optional[Any] = None
    volume: Optional[int] = None
