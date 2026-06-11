"""User trade endpoints backed by Supabase."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_supabase_user
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import ApiResponse, TradeCreate, TradeUpdate
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=ApiResponse)
async def list_trades(
    client_id: int | None = None,
    status_filter: str | None = Query(None, alias="status"),
    is_active: bool | None = Query(True),
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    rows = SupabaseDBService(db).list_rows(
        "user_trades",
        filters={"client_id": client_id, "status": status_filter, "is_active": is_active},
        order_by="confirm_date",
        desc=True,
    )
    return ApiResponse(message="Trades retrieved successfully", data=rows)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_trade(
    payload: TradeCreate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).create_row("user_trades", payload.model_dump(mode="json"))
    return ApiResponse(message="Trade created successfully", data=row)


@router.get("/{trade_id}", response_model=ApiResponse)
async def get_trade(
    trade_id: int,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).get_by_id("user_trades", trade_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return ApiResponse(message="Trade retrieved successfully", data=row)


@router.patch("/{trade_id}", response_model=ApiResponse)
async def update_trade(
    trade_id: int,
    payload: TradeUpdate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).update_by_id(
        "user_trades",
        trade_id,
        payload.model_dump(mode="json", exclude_unset=True),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return ApiResponse(message="Trade updated successfully", data=row)
