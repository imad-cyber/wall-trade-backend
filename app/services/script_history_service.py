"""Script history service."""
from typing import Any, Optional

from app.repositories.script_history_repository import ScriptHistoryRepository


class ScriptHistoryService:
    def __init__(self, repo: ScriptHistoryRepository):
        self.repo = repo

    def list_history(
        self,
        *,
        commodity_id: Optional[int] = None,
        sector_id: Optional[int] = None,
        script_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self.repo.list(
            limit=limit,
            filters={
                "commodity_id": commodity_id,
                "sector_id": sector_id,
                "script_id": script_id,
            },
            order_by="history_date",
            desc=True,
        )

    def create_row(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repo.create(payload)

    def get_latest(self, script_id: int) -> Optional[dict[str, Any]]:
        return self.repo.get_latest_for_script(script_id)
