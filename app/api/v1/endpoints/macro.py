"""Macro market snapshot endpoint."""
from fastapi import APIRouter, Depends, status

from app.auth import get_current_supabase_user
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import ApiResponse
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def get_macro_snapshot(
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    """Return the latest cached macro snapshot from Supabase."""
    macro = SupabaseDBService(db).get_latest_macro()
    return ApiResponse(
        message="Macro snapshot retrieved successfully" if macro else "No macro snapshot found",
        data=macro,
    )


@router.get("/indicators", response_model=ApiResponse, status_code=status.HTTP_200_OK)
async def get_macro_indicators(
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    """Backward-compatible alias for the macro snapshot."""
    return await get_macro_snapshot(db=db, user=user)
