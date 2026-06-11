"""
Supabase table operations used by Wall-Trade endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from postgrest.exceptions import APIError

from app.core import get_logger
from app.core.exceptions import AppException

logger = get_logger(__name__)


class SupabaseDBService:
    """Small repository-style wrapper around Supabase query builder."""

    def __init__(self, db_client):
        self.db = db_client

    @staticmethod
    def _data(response) -> Any:
        return getattr(response, "data", response)

    @staticmethod
    def _execute(query):
        try:
            return query.execute()
        except APIError as exc:
            code = getattr(exc, "code", None)
            payload = getattr(exc, "args", [{}])[0] if getattr(exc, "args", None) else {}
            if isinstance(payload, dict):
                code = payload.get("code", code)
                message = payload.get("message", str(exc))
            else:
                message = str(exc)
            if code == "42501":
                raise AppException(
                    "Supabase table access is denied. Send a valid Supabase user JWT "
                    "in the Authorization header or adjust RLS policies for this role.",
                    status_code=503,
                    error_code="SUPABASE_CONFIGURATION_ERROR",
                )
            raise AppException(
                f"Supabase query failed: {message}",
                status_code=502,
                error_code="SUPABASE_QUERY_ERROR",
            )

    def list_rows(
        self,
        table: str,
        *,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> list[dict[str, Any]]:
        query = self.db.table(table).select("*")
        for key, value in (filters or {}).items():
            if value is not None:
                query = query.eq(key, value)
        if order_by:
            query = query.order(order_by, desc=desc)
        response = self._execute(query.range(offset, offset + limit - 1))
        return self._data(response) or []

    def get_by_id(self, table: str, row_id: Any, id_column: str = "id") -> Optional[dict[str, Any]]:
        response = self._execute(self.db.table(table).select("*").eq(id_column, row_id).limit(1))
        rows = self._data(response) or []
        return rows[0] if rows else None

    def create_row(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._execute(self.db.table(table).insert(payload))
        rows = self._data(response) or []
        return rows[0] if rows else {}

    def update_by_id(self, table: str, row_id: Any, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        clean_payload = {key: value for key, value in payload.items() if value is not None}
        query = (
            self.db.table(table)
            .update(clean_payload)
            .eq("id", row_id)
        )
        response = self._execute(query)
        rows = self._data(response) or []
        return rows[0] if rows else None

    def get_latest_macro(self) -> Optional[dict[str, Any]]:
        rows = self.list_rows("macro_cache", limit=1, order_by="updated_at", desc=True)
        return rows[0] if rows else None

    def get_analysis_cache(self, ticker: str) -> Optional[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        query = (
            self.db.table("analysis_cache")
            .select("*")
            .eq("ticker", ticker.upper())
            .gt("expires_at", now)
            .order("generated_at", desc=True)
            .limit(1)
        )
        response = self._execute(query)
        rows = self._data(response) or []
        return rows[0] if rows else None

    def upsert_analysis_cache(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        payload.setdefault("generated_at", now.isoformat())
        payload.setdefault("expires_at", (now + timedelta(hours=24)).isoformat())
        payload["ticker"] = payload["ticker"].upper()
        response = self._execute(self.db.table("analysis_cache").insert(payload))
        rows = self._data(response) or []
        return rows[0] if rows else {}
