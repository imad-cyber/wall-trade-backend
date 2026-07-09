"""Search endpoints — S1, S2."""
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_search_service
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_optional_user
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/symbols", status_code=status.HTTP_200_OK)
async def search_symbols(
    q: str = Query("", min_length=0),
    exchange: str = Query("PSX"),
    limit: int = Query(25, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
    user=Depends(get_optional_user),
):
    """S1 — Symbol autocomplete."""
    result = await service.search_symbols(q, exchange, limit)
    return make_response(result.model_dump(mode="json"))


@router.get("/news", status_code=status.HTTP_200_OK)
async def search_news(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
    user=Depends(get_optional_user),
):
    """S2 — News search."""
    result = await service.search_news(q, limit)
    return make_response(result)
