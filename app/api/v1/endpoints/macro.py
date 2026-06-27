"""Macro market snapshot endpoint."""
from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_macro_service
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_current_supabase_user
from app.services.macro_service import MacroService

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_macro_snapshot(
    service: MacroService = Depends(get_macro_service),
    user=Depends(get_current_supabase_user),
):
    macro = service.get_latest()
    data = macro.model_dump(mode="json") if macro else None
    return make_response(data, cache_hit=macro is not None)


@router.get("/indicators", status_code=status.HTTP_200_OK)
async def get_macro_indicators(
    service: MacroService = Depends(get_macro_service),
    user=Depends(get_current_supabase_user),
):
    return await get_macro_snapshot(service=service, user=user)
