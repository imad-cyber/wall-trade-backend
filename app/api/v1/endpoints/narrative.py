"""Narrative intelligence endpoints — NI1 through NI13."""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_narrative_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_current_supabase_user
from app.auth.supabase_auth import validate_supabase_token_query
from app.core.config import get_settings
from app.services.narrative_service import NarrativeService

router = APIRouter(prefix="/narrative", tags=["narrative"])


@router.get("/tickers", status_code=status.HTTP_200_OK)
async def get_narrative_tickers(
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI1 — Tracked tickers."""
    result = service.get_tracked_tickers()
    return make_response(result.model_dump(mode="json"))


@router.get("/trending", status_code=status.HTTP_200_OK)
async def get_narrative_trending(
    limit: int = Query(8, ge=1, le=50),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI3 — Trending narratives."""
    return make_response(service.get_trending(limit))


@router.get("/traps", status_code=status.HTTP_200_OK)
async def get_narrative_traps(
    limit: int = Query(20, ge=1, le=100),
    verdict: str = Query("all"),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI4 — Narrative traps."""
    return make_response(service.get_traps(limit, verdict))


@router.get("/coordination", status_code=status.HTTP_200_OK)
async def get_coordination(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI6 — Coordination flags."""
    return make_response(service.get_coordination(limit))


@router.get("/ecosystem/tickers", status_code=status.HTTP_200_OK)
async def get_ecosystem_tickers(
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI7 — Ecosystem tickers."""
    return make_response(service.get_ecosystem_tickers())


@router.get("/ecosystem/themes", status_code=status.HTTP_200_OK)
async def get_ecosystem_themes(
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI8 — Ecosystem themes."""
    return make_response(service.get_ecosystem_themes())


@router.get("/network", status_code=status.HTTP_200_OK)
async def get_influence_network(
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI9 — Influence network."""
    result = service.get_network()
    return make_response(result.model_dump(mode="json"))


@router.get("/hero-stats", status_code=status.HTTP_200_OK)
async def get_hero_stats(
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI10 — Hero statistics."""
    result = service.get_hero_stats()
    return make_response(result.model_dump(mode="json"))


@router.get("/dying", status_code=status.HTTP_200_OK)
async def get_dying_narratives(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI11 — Decaying narratives."""
    return make_response(service.get_dying(limit))


@router.get("/scorecard", status_code=status.HTTP_200_OK)
async def get_narrative_scorecard(
    limit: int = Query(20, ge=1, le=100),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI12 — Weekly scorecard."""
    return make_response(service.get_scorecard(limit))


@router.get("/stream")
async def stream_narrative_updates(
    token: str = Query(...),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI13 — SSE narrative stream."""
    settings = get_settings()
    user = validate_supabase_token_query(token, settings)
    return StreamingResponse(
        service.stream_updates(user["user_id"]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{ticker}/timeline", status_code=status.HTTP_200_OK)
async def get_narrative_timeline(
    ticker: str = TickerPath(),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI5 — Narrative timeline."""
    normalized = validate_ticker(ticker)
    result = await service.get_timeline(normalized)
    return make_response(result.model_dump(mode="json"))


@router.get("/{ticker}", status_code=status.HTTP_200_OK)
async def get_unified_narrative(
    ticker: str = TickerPath(),
    user=Depends(get_current_supabase_user),
    service: NarrativeService = Depends(get_narrative_service),
):
    """NI2 — Unified ticker narrative."""
    normalized = validate_ticker(ticker)
    result = service.get_unified(normalized)
    return make_response(result.model_dump(mode="json"))
