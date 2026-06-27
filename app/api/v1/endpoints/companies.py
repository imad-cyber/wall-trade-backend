"""Company profile and metrics endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_company_service
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_current_supabase_user
from app.services.company_service import CompanyService

router = APIRouter(tags=["companies"])


@router.get("/company/{ticker}", status_code=status.HTTP_200_OK)
async def get_company_by_ticker(
    ticker: str,
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_current_supabase_user),
):
    missing = service.missing_config()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "errors": [{"code": "SERVICE_UNAVAILABLE", "message": "Capital Stake is not configured."}],
                "missing_configuration": missing,
            },
        )
    profile = await service.get_company_profile(ticker)
    return make_response(profile.model_dump(mode="json"))


@router.get("/companies/{ticker}", include_in_schema=False)
async def get_company_legacy(
    ticker: str,
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_current_supabase_user),
):
    return await get_company_by_ticker(ticker=ticker, service=service, user=user)
