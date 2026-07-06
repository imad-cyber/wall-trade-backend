"""Search response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str = "PSX"
    type: Literal["stock", "etf", "index", "crypto", "forex", "commodity"] = "stock"
    currency: str = "PKR"
    logo_url: Optional[str] = None


class SymbolSearchResponse(BaseModel):
    query: str
    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0


class NewsSearchResponse(BaseModel):
    query: str
    articles: list[dict] = Field(default_factory=list)
    total: int = 0
