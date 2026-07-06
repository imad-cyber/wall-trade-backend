"""Reports repository — ticker_reports table."""
from typing import Any, Optional

from app.repositories.base import BaseRepository


class ReportsRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "ticker_reports")

    def list_reports(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return self.list(limit=limit, order_by="published_at", desc=True)

    def get_by_id(self, report_id: str) -> Optional[dict[str, Any]]:
        return super().get_by_id(report_id)

    def record_access(self, report_id: str, email: str) -> None:
        self.db.table("report_access_log").insert({
            "report_id": report_id,
            "email": email.lower(),
        }).execute()
