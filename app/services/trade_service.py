"""Trade business logic service."""
from typing import Any, Optional

from app.repositories.trade_repository import TradeRepository


class TradeService:
    def __init__(self, repo: TradeRepository):
        self.repo = repo

    def list_trades(
        self,
        *,
        client_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> list[dict[str, Any]]:
        return self.repo.list(
            filters={"client_id": client_id, "status": status, "is_active": is_active},
            order_by="confirm_date",
            desc=True,
        )

    def get_trade(self, trade_id: int) -> Optional[dict[str, Any]]:
        return self.repo.get_by_id(trade_id)

    def create_trade(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repo.create(payload)

    def update_trade(self, trade_id: int, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        return self.repo.update(trade_id, payload)
