"""Script history endpoints."""
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_script_history_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas_walltrade import ScriptHistoryCreate
from app.auth.dependencies import get_current_supabase_user
from app.services.script_history_service import ScriptHistoryService

router = APIRouter(prefix="/script-history", tags=["script-history"])


@router.get("")
async def list_script_history(
    commodity_id: int | None = None,
    sector_id: int | None = None,
    script_id: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    service: ScriptHistoryService = Depends(get_script_history_service),
    user=Depends(get_current_supabase_user),
):
    rows = service.list_history(
        commodity_id=commodity_id,
        sector_id=sector_id,
        script_id=script_id,
        limit=limit,
    )
    return make_response(rows)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_script_history(
    payload: ScriptHistoryCreate,
    service: ScriptHistoryService = Depends(get_script_history_service),
    user=Depends(get_current_supabase_user),
):
    row = service.create_row(payload.model_dump(mode="json"))
    return make_response(row)


@router.get("/latest/{script_id}")
async def get_latest_script_history(
    script_id: int,
    service: ScriptHistoryService = Depends(get_script_history_service),
    user=Depends(get_current_supabase_user),
):
    row = service.get_latest(script_id)
    return make_response(row)
