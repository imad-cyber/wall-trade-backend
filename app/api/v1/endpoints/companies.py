"""Company profile and metrics endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_supabase_user
from app.config import get_settings
from app.dependencies import get_settings_dependency
from app.api.v1.schemas_walltrade import ApiResponse, ServiceUnavailableResponse

router = APIRouter(tags=["companies"])


def _require_capital_stake() -> str:
    settings = get_settings()
    if not settings.capital_stake_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ServiceUnavailableResponse(
                message="Capital Stake integration is not configured yet.",
                missing_configuration=["CAPITAL_STAKE_API_KEY or CAPITAL_API_KEY"],
            ).model_dump(),
        )
    return settings.capital_stake_key


@router.get(
    "/company/{ticker}",
    response_model=ApiResponse,
    responses={503: {"model": ServiceUnavailableResponse}},
    status_code=status.HTTP_200_OK,
)
async def get_company_by_ticker(
    ticker: str,
    user=Depends(get_current_supabase_user),
    settings=Depends(get_settings_dependency),
):
    """Fetch company profile and key financial metrics from Capital Stake."""
    _require_capital_stake()
    return ApiResponse(
        message="Capital Stake is configured, but provider mapping is not implemented yet.",
        data={"ticker": ticker.upper()},
    )


@router.get("/companies/{ticker}", response_model=ApiResponse, include_in_schema=False)
async def get_company_legacy(ticker: str, user=Depends(get_current_supabase_user)):
    """Legacy alias for earlier repository route naming."""
    return await get_company_by_ticker(ticker=ticker, user=user)
