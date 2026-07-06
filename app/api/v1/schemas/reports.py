"""Reports response schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class ReportSummary(BaseModel):
    id: str
    ticker: str
    title: str
    summary: str = ""
    published_at: str
    report_text: Optional[str] = None


class ReportListResponse(BaseModel):
    reports: list[ReportSummary] = Field(default_factory=list)
    total: int = 0


class ReportAccessRequest(BaseModel):
    email: str


class ReportAccessResponse(BaseModel):
    success: bool = True
    report_text: str = ""


class ReportDetailResponse(BaseModel):
    id: str
    ticker: str
    title: str
    report_text: str
    published_at: str
