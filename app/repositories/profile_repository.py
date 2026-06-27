"""User profile repository."""
from typing import Any, Optional

from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "profiles")

    def get_by_user_id(self, user_id: str) -> Optional[dict[str, Any]]:
        rows = self.list(limit=1, filters={"id": user_id})
        return rows[0] if rows else None

    def upsert(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_by_user_id(user_id)
        if existing:
            return self.update(user_id, payload, id_column="id") or existing
        payload["id"] = user_id
        return self.create(payload)
