"""Analysis cache repository."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import get_settings
from app.domain.analysis.models import AnalysisCache
from app.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "analysis_cache")

    def get_valid_cache(self, ticker: str) -> Optional[AnalysisCache]:
        now = datetime.now(timezone.utc).isoformat()
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("ticker", ticker.upper())
            .gt("expires_at", now)
            .order("generated_at", desc=True)
            .limit(1)
        )
        response = self._execute(query, operation="get_valid_cache")
        rows = self._data(response) or []
        return AnalysisCache.from_db_row(rows[0]) if rows else None

    def upsert_cache(self, cache: AnalysisCache) -> AnalysisCache:
        settings = get_settings()
        now = datetime.now(timezone.utc)
        payload = cache.to_db_payload()
        payload.setdefault("generated_at", now.isoformat())
        payload.setdefault(
            "expires_at",
            (now + timedelta(hours=settings.ANALYSIS_CACHE_TTL_HOURS)).isoformat(),
        )
        payload["ticker"] = payload["ticker"].upper()
        row = self.create(payload)
        return AnalysisCache.from_db_row(row)

    def create_cache_row(self, payload: dict) -> dict:
        return self.create(payload)
