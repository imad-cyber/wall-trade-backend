"""Market feel service."""
from typing import Any, Optional

from app.repositories.market_feel_repository import MarketFeelRepository


class MarketFeelService:
    def __init__(self, repo: MarketFeelRepository):
        self.repo = repo

    def list_entries(
        self,
        *,
        commodity_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return self.repo.list(
            limit=limit,
            filters={"commodity_id": commodity_id, "is_active": is_active},
            order_by="entry_date",
            desc=True,
        )

    def create_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repo.create(payload)
