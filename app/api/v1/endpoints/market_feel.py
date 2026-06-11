"""Market sentiment endpoints backed by Supabase."""
from fastapi import APIRouter, Depends, Query, status

from app.auth import get_current_supabase_user
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import ApiResponse, MarketFeelCreate
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/market-feel", tags=["market-feel"])


@router.get("", response_model=ApiResponse)
async def list_market_feel(
    commodity_id: int | None = None,
    is_active: bool | None = Query(True),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    rows = SupabaseDBService(db).list_rows(
        "market_feel",
        limit=limit,
        filters={"commodity_id": commodity_id, "is_active": is_active},
        order_by="entry_date",
        desc=True,
    )
    return ApiResponse(message="Market feel entries retrieved successfully", data=rows)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_market_feel(
    payload: MarketFeelCreate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).create_row("market_feel", payload.model_dump(mode="json"))
    return ApiResponse(message="Market feel entry created successfully", data=row)
