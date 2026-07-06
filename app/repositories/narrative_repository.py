"""Narrative intelligence repository — Walsh Supabase tables."""
from typing import Any, Optional

from app.repositories.base import BaseRepository


class NarrativeRepository(BaseRepository):
    def __init__(self, db_client):
        super().__init__(db_client, "dashboard_ticker_view")

    def get_tickers(self) -> list[str]:
        response = self._execute(
            self.db.table(self.table_name).select("ticker"),
            operation="get_tickers",
        )
        rows = self._data(response) or []
        return sorted({str(r["ticker"]).upper() for r in rows if r.get("ticker")})

    def get_unified(self, ticker: str) -> Optional[dict[str, Any]]:
        rows = self.list(limit=1, filters={"ticker": ticker.upper()})
        return rows[0] if rows else None

    def get_trending(self, limit: int = 8) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table(self.table_name)
            .select("*")
            .order("vms", desc=True)
            .limit(limit),
            operation="get_trending",
        )
        return self._data(response) or []

    def get_traps(self, limit: int = 20, verdict: str = "all") -> list[dict[str, Any]]:
        query = self.db.table(self.table_name).select("*").order("nrs", desc=True).limit(limit)
        if verdict != "all":
            query = query.eq("verdict", verdict)
        response = self._execute(query, operation="get_traps")
        return self._data(response) or []

    def get_coordination(self, limit: int = 20) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table("coordination_flags")
            .select("*")
            .order("danger_score", desc=True)
            .limit(limit),
            operation="get_coordination",
        )
        return self._data(response) or []

    def get_ecosystem_tickers(self) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table("ticker_summary").select("*"),
            operation="get_ecosystem_tickers",
        )
        return self._data(response) or []

    def get_ecosystem_themes(self) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table("theme_summary").select("*"),
            operation="get_ecosystem_themes",
        )
        return self._data(response) or []

    def get_network(self) -> tuple[list[dict], list[dict]]:
        nodes_resp = self._execute(
            self.db.table("influence_nodes").select("*"),
            operation="get_network_nodes",
        )
        edges_resp = self._execute(
            self.db.table("influence_edges").select("*"),
            operation="get_network_edges",
        )
        return self._data(nodes_resp) or [], self._data(edges_resp) or []

    def get_hero_stats(self) -> dict[str, Any]:
        tickers = self.list(limit=1000)
        coord = self.get_coordination(limit=1000)
        traps = [t for t in tickers if t.get("verdict") in ("trap", "TRAP")]
        vms_scores = [float(t["vms"]) for t in tickers if t.get("vms") is not None]
        avg_vms = sum(vms_scores) / len(vms_scores) if vms_scores else 0.0
        from datetime import datetime, timezone
        return {
            "total_narratives_monitored": len(tickers),
            "active_coordination_flags": len(coord),
            "traps_detected_30d": len(traps),
            "avg_vms_score": round(avg_vms, 2),
            "market_health_score": round(100 - avg_vms * 0.3, 2),
            "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

    def get_dying(self, limit: int = 20) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table("decay_metrics")
            .select("*")
            .order("decay_rate", desc=True)
            .limit(limit),
            operation="get_dying",
        )
        return self._data(response) or []

    def get_scorecard(self, limit: int = 20) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table(self.table_name)
            .select("*")
            .order("date", desc=True)
            .limit(limit),
            operation="get_scorecard",
        )
        return self._data(response) or []

    def get_timeline_stories(self, ticker: str) -> list[dict[str, Any]]:
        response = self._execute(
            self.db.table("narrative_analyses")
            .select("*")
            .eq("ticker", ticker.upper())
            .order("date", desc=True),
            operation="get_timeline_stories",
        )
        return self._data(response) or []
