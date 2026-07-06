"""User alerts repository."""
from typing import Any

from app.repositories.base import BaseRepository


class AlertsRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "user_alerts")

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        return self.list(filters={"user_id": user_id}, order_by="created_at", desc=True)

    def create_alert(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload["user_id"] = user_id
        return self.create(payload)

    def delete_alert(self, user_id: str, alert_id: str) -> bool:
        response = self._execute(
            self.db.table(self.table_name)
            .delete()
            .eq("user_id", user_id)
            .eq("id", alert_id),
            operation="delete_alert",
        )
        rows = self._data(response) or []
        return bool(rows)
