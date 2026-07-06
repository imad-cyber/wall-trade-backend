"""News response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


NewsCategory = Literal[
    "Recent", "Analysis", "Earnings", "Transcripts", "Company",
    "Analyst Ratings", "Insider Trading", "SEC Filings", "Pro",
]


class NewsThumbnail(BaseModel):
    bg: str = "#1e293b"
    label: str = ""


class NewsArticle(BaseModel):
    id: str
    headline: str
    source: str
    published_at: str
    time_ago: str = ""
    is_pro: bool = False
    category: str = "Recent"
    url: Optional[str] = None
    thumbnail: NewsThumbnail = Field(default_factory=NewsThumbnail)


class NewsResponse(BaseModel):
    ticker: str
    active_category: str = "Recent"
    categories: list[str] = Field(default_factory=list)
    articles: list[NewsArticle] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
