"""AI analysis response schemas."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AIAnalyzeRequest(BaseModel):
    analysis_type: Literal["full", "quick", "technical", "narrative"] = "full"
    model: Optional[str] = "gpt-4o"


class AIAnalyzeResponse(BaseModel):
    job_id: str
    ticker: str
    status: str = "queued"
    stream_url: str


class AIReportResponse(BaseModel):
    ticker: str
    analysis: dict = Field(default_factory=dict)
    generated_at: Optional[str] = None
