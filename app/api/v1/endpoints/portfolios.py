"""User portfolio endpoints backed by Supabase."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_supabase_user
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import ApiResponse, PortfolioCreate, PortfolioUpdate
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=ApiResponse)
async def list_portfolios(
    client_id: int | None = None,
    is_active: bool | None = Query(True),
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    rows = SupabaseDBService(db).list_rows(
        "user_portfolio",
        filters={"client_id": client_id, "is_active": is_active},
        order_by="id",
        desc=True,
    )
    return ApiResponse(message="Portfolios retrieved successfully", data=rows)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).create_row("user_portfolio", payload.model_dump(mode="json"))
    return ApiResponse(message="Portfolio created successfully", data=row)


@router.get("/{portfolio_id}", response_model=ApiResponse)
async def get_portfolio(
    portfolio_id: int,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).get_by_id("user_portfolio", portfolio_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return ApiResponse(message="Portfolio retrieved successfully", data=row)


@router.patch("/{portfolio_id}", response_model=ApiResponse)
async def update_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).update_by_id(
        "user_portfolio",
        portfolio_id,
        payload.model_dump(mode="json", exclude_unset=True),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return ApiResponse(message="Portfolio updated successfully", data=row)
