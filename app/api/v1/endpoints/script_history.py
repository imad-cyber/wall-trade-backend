"""Script history endpoints backed by Supabase."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.auth import get_current_supabase_user
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import ApiResponse, ScriptHistoryCreate
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/script-history", tags=["script-history"])


@router.get("", response_model=ApiResponse)
async def list_script_history(
    commodity_id: int | None = None,
    sector_id: int | None = None,
    script_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    rows = SupabaseDBService(db).list_rows(
        "script_history",
        limit=limit,
        filters={
            "commodity_id": commodity_id,
            "sector_id": sector_id,
            "script_id": script_id,
        },
        order_by="history_date",
        desc=True,
    )
    return ApiResponse(message="Script history retrieved successfully", data=rows)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_script_history(
    payload: ScriptHistoryCreate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    row = SupabaseDBService(db).create_row("script_history", payload.model_dump(mode="json"))
    return ApiResponse(message="Script history row created successfully", data=row)


@router.get("/latest/{script_id}", response_model=ApiResponse)
async def get_latest_script_history(
    script_id: int,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    rows = SupabaseDBService(db).list_rows(
        "script_history",
        limit=1,
        filters={"script_id": script_id},
        order_by="history_date",
        desc=True,
    )
    return ApiResponse(
        message="Latest script history retrieved successfully" if rows else "No history found",
        data=rows[0] if rows else None,
    )
