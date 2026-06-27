"""User trade endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.dependencies import get_trade_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas_walltrade import TradeCreate, TradeUpdate
from app.auth.dependencies import get_current_supabase_user
from app.services.trade_service import TradeService

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("")
async def list_trades(
    client_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    is_active: bool | None = Query(True),
    service: TradeService = Depends(get_trade_service),
    user=Depends(get_current_supabase_user),
):
    rows = service.list_trades(client_id=client_id, status=status_filter, is_active=is_active)
    return make_response(rows)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_trade(
    payload: TradeCreate,
    service: TradeService = Depends(get_trade_service),
    user=Depends(get_current_supabase_user),
):
    row = service.create_trade(payload.model_dump(mode="json"))
    return make_response(row)


@router.get("/{trade_id}")
async def get_trade(
    trade_id: int,
    service: TradeService = Depends(get_trade_service),
    user=Depends(get_current_supabase_user),
):
    row = service.get_trade(trade_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return make_response(row)


@router.patch("/{trade_id}")
async def update_trade(
    trade_id: int,
    payload: TradeUpdate,
    service: TradeService = Depends(get_trade_service),
    user=Depends(get_current_supabase_user),
):
    row = service.update_trade(trade_id, payload.model_dump(mode="json", exclude_unset=True))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return make_response(row)
