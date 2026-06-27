"""AI stock-analysis endpoints."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_analysis_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas_walltrade import AnalysisCacheCreate
from app.auth.dependencies import get_current_supabase_user
from app.observability.context import get_ctx
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyse", tags=["analysis"])


@router.get("/{ticker}")
async def analyse_ticker(
    ticker: str,
    refresh: bool = Query(False, description="Force a fresh AI analysis instead of cache"),
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_current_supabase_user),
):
    """Return cached analysis JSON or stream a fresh analysis via SSE."""
    if not refresh:
        cached = service.get_cached_analysis(ticker)
        if cached:
            get_ctx().cache_hit = True
            return make_response(cached.model_dump(mode="json"), cache_hit=True)

    missing = service.missing_config()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "errors": [{"code": "SERVICE_UNAVAILABLE", "message": "AI analysis is not configured yet."}],
                "missing_configuration": missing,
            },
        )

    return StreamingResponse(
        service.stream_analysis(ticker, refresh=refresh),
        media_type="text/event-stream",
    )


@router.post("/cache", status_code=status.HTTP_201_CREATED)
async def create_analysis_cache(
    payload: AnalysisCacheCreate,
    service: AnalysisService = Depends(get_analysis_service),
    user=Depends(get_current_supabase_user),
):
    """Create an analysis_cache row for testing/admin workflows."""
    now = datetime.now(timezone.utc)
    row = payload.model_dump(mode="json")
    row["ticker"] = row["ticker"].upper()
    row.setdefault("generated_at", now.isoformat())
    row["expires_at"] = row.get("expires_at") or (now + timedelta(hours=24)).isoformat()
    created = service.create_cache_row(row)
    return make_response(created)
