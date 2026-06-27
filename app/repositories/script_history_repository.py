"""Script history repository."""
from app.repositories.base import BaseRepository


class ScriptHistoryRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "script_history")

    def get_latest_for_script(self, script_id: int) -> dict | None:
        rows = self.list(limit=1, filters={"script_id": script_id}, order_by="history_date", desc=True)
        return rows[0] if rows else None
