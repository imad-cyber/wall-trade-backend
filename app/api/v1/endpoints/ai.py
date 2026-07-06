"""AI analysis endpoints — AI1, AI2, AI3."""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_ai_service
from app.api.v1.schemas.ai import AIAnalyzeRequest
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_current_supabase_user
from app.auth.supabase_auth import validate_supabase_token_query
from app.core.config import get_settings
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze/{ticker}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ai_analysis(
    ticker: str = TickerPath(),
    body: AIAnalyzeRequest = AIAnalyzeRequest(),
    user=Depends(get_current_supabase_user),
    service: AIService = Depends(get_ai_service),
):
    """AI1 — Trigger AI analysis job."""
    normalized = validate_ticker(ticker)
    result = service.trigger_analysis(normalized, body)
    return make_response(result.model_dump(mode="json"))


@router.get("/stream/{ticker}")
async def stream_ai_analysis(
    ticker: str = TickerPath(),
    job_id: str | None = Query(None),
    token: str | None = Query(None),
    user=Depends(get_current_supabase_user),
    service: AIService = Depends(get_ai_service),
):
    """AI2 — SSE AI analysis stream."""
    if token:
        validate_supabase_token_query(token, get_settings())
    normalized = validate_ticker(ticker)
    return StreamingResponse(
        service.stream_analysis(normalized, job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/report/{ticker}", status_code=status.HTTP_200_OK)
async def get_ai_report(
    ticker: str = TickerPath(),
    user=Depends(get_current_supabase_user),
    service: AIService = Depends(get_ai_service),
):
    """AI3 — Last cached AI analysis."""
    normalized = validate_ticker(ticker)
    result = service.get_last_report(normalized)
    return make_response(result.model_dump(mode="json"))
