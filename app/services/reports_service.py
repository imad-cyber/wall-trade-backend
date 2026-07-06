"""Reports service — R1, R2, R3."""
from app.api.v1.schemas.reports import ReportDetailResponse, ReportListResponse, ReportSummary
from app.core.exceptions import ResourceNotFoundError
from app.repositories.reports_repository import ReportsRepository


class ReportsService:
    def __init__(self, repo: ReportsRepository):
        self.repo = repo

    def list_reports(self, *, authenticated: bool = False) -> ReportListResponse:
        rows = self.repo.list_reports()
        reports: list[ReportSummary] = []
        for row in rows:
            text = row.get("report_text", "")
            reports.append(ReportSummary(
                id=str(row.get("id", "")),
                ticker=str(row.get("ticker", "")),
                title=str(row.get("title", "")),
                summary=str(row.get("summary", ""))[:200],
                published_at=str(row.get("published_at", "")),
                report_text=text if authenticated else None,
            ))
        return ReportListResponse(reports=reports, total=len(reports))

    def access_report(self, report_id: str, email: str) -> str:
        row = self.repo.get_by_id(report_id)
        if not row:
            raise ResourceNotFoundError(f"Report {report_id}")
        self.repo.record_access(report_id, email)
        return str(row.get("report_text", ""))

    def get_full_report(self, report_id: str) -> ReportDetailResponse:
        row = self.repo.get_by_id(report_id)
        if not row:
            raise ResourceNotFoundError(f"Report {report_id}")
        return ReportDetailResponse(
            id=str(row.get("id", "")),
            ticker=str(row.get("ticker", "")),
            title=str(row.get("title", "")),
            report_text=str(row.get("report_text", "")),
            published_at=str(row.get("published_at", "")),
        )
