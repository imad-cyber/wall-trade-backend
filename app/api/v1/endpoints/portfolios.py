"""User portfolio endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.dependencies import get_portfolio_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas_walltrade import PortfolioCreate, PortfolioUpdate
from app.auth.dependencies import get_current_supabase_user
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("")
async def list_portfolios(
    client_id: int | None = None,
    is_active: bool | None = Query(True),
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_supabase_user),
):
    rows = service.list_portfolios(client_id=client_id, is_active=is_active)
    return make_response(rows)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_supabase_user),
):
    row = service.create_portfolio(payload.model_dump(mode="json"))
    return make_response(row)


@router.get("/{portfolio_id}")
async def get_portfolio(
    portfolio_id: int,
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_supabase_user),
):
    row = service.get_portfolio(portfolio_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return make_response(row)


@router.patch("/{portfolio_id}")
async def update_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    service: PortfolioService = Depends(get_portfolio_service),
    user=Depends(get_current_supabase_user),
):
    row = service.update_portfolio(portfolio_id, payload.model_dump(mode="json", exclude_unset=True))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return make_response(row)
