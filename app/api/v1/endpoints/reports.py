"""Reports endpoints — R1, R2, R3."""
from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_reports_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas.reports import ReportAccessRequest
from app.auth.dependencies import get_current_supabase_user, get_optional_user
from app.services.reports_service import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_reports(
    service: ReportsService = Depends(get_reports_service),
    user=Depends(get_optional_user),
):
    """R1 — Public report list (truncated for unauthenticated)."""
    result = service.list_reports(authenticated=user is not None)
    return make_response(result.model_dump(mode="json"))


@router.post("/{report_id}/access", status_code=status.HTTP_200_OK)
async def access_report(
    report_id: str,
    body: ReportAccessRequest,
    service: ReportsService = Depends(get_reports_service),
):
    """R2 — Email gate for full report."""
    text = service.access_report(report_id, body.email)
    return make_response({"success": True, "report_text": text})


@router.get("/{report_id}", status_code=status.HTTP_200_OK)
async def get_full_report(
    report_id: str,
    service: ReportsService = Depends(get_reports_service),
    user=Depends(get_current_supabase_user),
):
    """R3 — Full report (auth required)."""
    result = service.get_full_report(report_id)
    return make_response(result.model_dump(mode="json"))
