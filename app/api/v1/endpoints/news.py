"""News endpoints — N1, N2."""
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_news_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_optional_user
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/market", status_code=status.HTTP_200_OK)
async def get_market_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
    user=Depends(get_optional_user),
):
    """N2 — Market-wide news."""
    result, cache_hit, cache_age = await service.get_market_news(page, page_size, user)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}", status_code=status.HTTP_200_OK)
async def get_ticker_news(
    ticker: str = TickerPath(),
    category: str = Query("Recent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
    user=Depends(get_optional_user),
):
    """N1 — Paginated ticker news."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_ticker_news(
        normalized, category, page, page_size, user,
    )
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


