"""User alerts service — AL1 through AL4."""
import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator
from uuid import uuid4

from app.api.v1.schemas.alerts import AlertCreateRequest, AlertItem, AlertListResponse
from app.core.exceptions import ResourceNotFoundError
from app.repositories.alerts_repository import AlertsRepository


class AlertsService:
    def __init__(self, repo: AlertsRepository):
        self.repo = repo

    def list_alerts(self, user_id: str) -> AlertListResponse:
        rows = self.repo.list_for_user(user_id)
        alerts = [
            AlertItem(
                id=str(r.get("id", "")),
                ticker=str(r.get("ticker", "")),
                alert_type=r.get("alert_type", "price_above"),
                threshold=float(r.get("threshold", 0)),
                is_active=bool(r.get("is_active", True)),
                created_at=str(r.get("created_at", "")),
                triggered_at=r.get("triggered_at"),
            )
            for r in rows
        ]
        return AlertListResponse(alerts=alerts)

    def create_alert(self, user_id: str, data: AlertCreateRequest) -> AlertItem:
        row = self.repo.create_alert(user_id, {
            "id": str(uuid4()),
            "ticker": data.ticker.upper(),
            "alert_type": data.alert_type,
            "threshold": data.threshold,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return AlertItem(
            id=str(row.get("id", "")),
            ticker=str(row.get("ticker", "")),
            alert_type=row.get("alert_type", "price_above"),
            threshold=float(row.get("threshold", 0)),
            is_active=True,
            created_at=str(row.get("created_at", "")),
        )

    def delete_alert(self, user_id: str, alert_id: str) -> None:
        if not self.repo.delete_alert(user_id, alert_id):
            raise ResourceNotFoundError(f"Alert {alert_id}")

    async def stream_alerts(self, user_id: str) -> AsyncIterator[str]:
        try:
            while True:
                yield ": ping\n\n"
                alerts = self.list_alerts(user_id)
                yield f"event: alert_status\ndata: {json.dumps({'count': len(alerts.alerts)})}\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            yield f"event: stream_end\ndata: {json.dumps({'reason': 'client_disconnect'})}\n\n"
