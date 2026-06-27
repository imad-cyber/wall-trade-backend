"""Portfolio business logic service."""
from typing import Any, Optional

from app.repositories.portfolio_repository import PortfolioRepository


class PortfolioService:
    def __init__(self, repo: PortfolioRepository):
        self.repo = repo

    def list_portfolios(
        self,
        *,
        client_id: Optional[int] = None,
        is_active: Optional[bool] = True,
    ) -> list[dict[str, Any]]:
        return self.repo.list(
            filters={"client_id": client_id, "is_active": is_active},
            order_by="id",
            desc=True,
        )

    def get_portfolio(self, portfolio_id: int) -> Optional[dict[str, Any]]:
        return self.repo.get_by_id(portfolio_id)

    def create_portfolio(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repo.create(payload)

    def update_portfolio(self, portfolio_id: int, payload: dict[str, Any]) -> Optional[dict[str, Any]]:
        return self.repo.update(portfolio_id, payload)
