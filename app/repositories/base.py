"""Base repository with generic CRUD operations."""
from typing import Any, Optional

from app.providers.supabase.executor import execute_query, extract_response_data


class BaseRepository:
    """Generic Supabase repository base class."""

    def __init__(self, db_client, table_name: str):
        self.db = db_client
        self.table_name = table_name

    def _data(self, response) -> Any:
        return extract_response_data(response)

    def _execute(self, query, *, operation: str = "query"):
        return execute_query(query, table=self.table_name, operation=operation)

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> list[dict[str, Any]]:
        query = self.db.table(self.table_name).select("*")
        for key, value in (filters or {}).items():
            if value is not None:
                query = query.eq(key, value)
        if order_by:
            query = query.order(order_by, desc=desc)
        response = self._execute(query.range(offset, offset + limit - 1), operation="list")
        return self._data(response) or []

    def get_by_id(self, row_id: Any, id_column: str = "id") -> Optional[dict[str, Any]]:
        response = self._execute(
            self.db.table(self.table_name).select("*").eq(id_column, row_id).limit(1),
            operation="get_by_id",
        )
        rows = self._data(response) or []
        return rows[0] if rows else None

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._execute(
            self.db.table(self.table_name).insert(payload),
            operation="create",
        )
        rows = self._data(response) or []
        return rows[0] if rows else {}

    def update(self, row_id: Any, payload: dict[str, Any], id_column: str = "id") -> Optional[dict[str, Any]]:
        clean_payload = {k: v for k, v in payload.items() if v is not None}
        response = self._execute(
            self.db.table(self.table_name).update(clean_payload).eq(id_column, row_id),
            operation="update",
        )
        rows = self._data(response) or []
        return rows[0] if rows else None
