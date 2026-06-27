"""Sector sentiment endpoints."""
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_sector_feel_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas_walltrade import SectorFeelCreate
from app.auth.dependencies import get_current_supabase_user
from app.services.sector_feel_service import SectorFeelService

router = APIRouter(prefix="/sector-feel", tags=["sector-feel"])


@router.get("")
async def list_sector_feel(
    commodity_id: int | None = None,
    is_active: bool | None = Query(True),
    limit: int = Query(20, ge=1, le=100),
    service: SectorFeelService = Depends(get_sector_feel_service),
    user=Depends(get_current_supabase_user),
):
    rows = service.list_entries(commodity_id=commodity_id, is_active=is_active, limit=limit)
    return make_response(rows)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_sector_feel(
    payload: SectorFeelCreate,
    service: SectorFeelService = Depends(get_sector_feel_service),
    user=Depends(get_current_supabase_user),
):
    row = service.create_entry(payload.model_dump(mode="json"))
    return make_response(row)
