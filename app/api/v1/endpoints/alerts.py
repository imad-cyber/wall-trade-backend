"""User alerts endpoints — AL1 through AL4."""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_alerts_service
from app.api.v1.schemas.alerts import AlertCreateRequest
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_current_supabase_user
from app.auth.supabase_auth import validate_supabase_token_query
from app.core.config import get_settings
from app.services.alerts_service import AlertsService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_alerts(
    user=Depends(get_current_supabase_user),
    service: AlertsService = Depends(get_alerts_service),
):
    """AL1 — List user alerts."""
    result = service.list_alerts(user["user_id"])
    return make_response(result.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreateRequest,
    user=Depends(get_current_supabase_user),
    service: AlertsService = Depends(get_alerts_service),
):
    """AL2 — Create alert."""
    from app.api.v1.validators import validate_ticker
    validate_ticker(body.ticker)
    result = service.create_alert(user["user_id"], body)
    return make_response(result.model_dump(mode="json"))


@router.delete("/{alert_id}", status_code=status.HTTP_200_OK)
async def delete_alert(
    alert_id: str,
    user=Depends(get_current_supabase_user),
    service: AlertsService = Depends(get_alerts_service),
):
    """AL3 — Delete alert."""
    service.delete_alert(user["user_id"], alert_id)
    return make_response({"deleted": alert_id})


@router.get("/stream")
async def stream_alerts(
    token: str = Query(...),
    service: AlertsService = Depends(get_alerts_service),
):
    """AL4 — SSE alert stream."""
    settings = get_settings()
    user = validate_supabase_token_query(token, settings)
    return StreamingResponse(
        service.stream_alerts(user["user_id"]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
