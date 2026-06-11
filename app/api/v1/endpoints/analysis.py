"""AI stock-analysis endpoints."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.auth import get_current_supabase_user
from app.config import get_settings
from app.dependencies import get_db_dependency
from app.api.v1.schemas_walltrade import (
    AnalysisCacheCreate,
    ApiResponse,
    ServiceUnavailableResponse,
)
from app.services.supabase_db import SupabaseDBService

router = APIRouter(prefix="/analyse", tags=["analysis"])


def _missing_analysis_config() -> list[str]:
    settings = get_settings()
    missing = []
    if not settings.AI_API_KEY:
        missing.append("AI_API_KEY")
    if not settings.capital_stake_key:
        missing.append("CAPITAL_STAKE_API_KEY or CAPITAL_API_KEY")
    return missing


@router.get(
    "/{ticker}",
    responses={
        200: {"description": "Cached JSON analysis or text/event-stream for a fresh run"},
        503: {"model": ServiceUnavailableResponse},
    },
)
async def analyse_ticker(
    ticker: str,
    refresh: bool = Query(False, description="Force a fresh AI analysis instead of cache"),
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    """
    Return cached analysis, or stream a fresh analysis when external keys are configured.
    """
    service = SupabaseDBService(db)
    cached = None if refresh else service.get_analysis_cache(ticker)
    if cached:
        return ApiResponse(message="Cached analysis retrieved successfully", data=cached)

    missing = _missing_analysis_config()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ServiceUnavailableResponse(
                message="AI analysis is not configured yet.",
                missing_configuration=missing,
            ).model_dump(),
        )

    async def event_stream():
        yield "event: status\ndata: Analysis provider mapping is not implemented yet.\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post(
    "/cache",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_cache(
    payload: AnalysisCacheCreate,
    db=Depends(get_db_dependency),
    user=Depends(get_current_supabase_user),
):
    """Create an analysis_cache row for testing/admin workflows."""
    now = datetime.now(timezone.utc)
    row = payload.model_dump(mode="json")
    row["ticker"] = row["ticker"].upper()
    row.setdefault("generated_at", now.isoformat())
    row["expires_at"] = row.get("expires_at") or (now + timedelta(hours=24)).isoformat()
    created = SupabaseDBService(db).create_row("analysis_cache", row)
    return ApiResponse(message="Analysis cache row created successfully", data=created)
