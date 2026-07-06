"""Contract analysis endpoints — A1 through A5."""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_analysis_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_current_supabase_user, get_optional_user
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{ticker}/analyst", status_code=status.HTTP_200_OK)
async def get_analyst_ratings(
    ticker: str = TickerPath(),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_optional_user),
):
    """A1 — Analyst consensus and ratings."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_analyst_ratings(normalized, page, limit)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/swot", status_code=status.HTTP_200_OK)
async def get_swot_analysis(
    ticker: str = TickerPath(),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_optional_user),
):
    """A2 — SWOT analysis (cached)."""
    normalized = validate_ticker(ticker)
    result, cache_hit = await service.get_swot(normalized)
    return make_response(result.model_dump(mode="json"), cache_hit=cache_hit)


@router.get("/{ticker}/technical", status_code=status.HTTP_200_OK)
async def get_technical_analysis(
    ticker: str = TickerPath(),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_optional_user),
):
    """A3 — Technical signals per timeframe."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_technical(normalized, user)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/earnings-call", status_code=status.HTTP_200_OK)
async def get_earnings_call(
    ticker: str = TickerPath(),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_optional_user),
):
    """A4 — Earnings call summary."""
    normalized = validate_ticker(ticker)
    result = await service.get_earnings_call(normalized)
    return make_response(result.model_dump(mode="json"))


@router.get("/{ticker}/scorecard", status_code=status.HTTP_200_OK)
async def get_analysis_scorecard(
    ticker: str = TickerPath(),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_current_supabase_user),
):
    """A5 — Narrative scorecard (auth required)."""
    normalized = validate_ticker(ticker)
    result = await service.get_scorecard(normalized, user["user_id"])
    return make_response(result)
