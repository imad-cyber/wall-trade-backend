"""Live price endpoints that proxy the PSX service when configured."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_supabase_user
from app.config import get_settings
from app.dependencies import get_settings_dependency
from app.api.v1.schemas_walltrade import ApiResponse, ServiceUnavailableResponse

router = APIRouter(prefix="/prices", tags=["prices"])


def _require_psx_proxy() -> str:
    settings = get_settings()
    if not settings.PSX_PROXY_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ServiceUnavailableResponse(
                message="PSX proxy integration is not configured yet.",
                missing_configuration=["PSX_PROXY_URL"],
            ).model_dump(),
        )
    return settings.PSX_PROXY_URL


@router.get(
    "/all",
    response_model=ApiResponse,
    responses={503: {"model": ServiceUnavailableResponse}},
    status_code=status.HTTP_200_OK,
)
async def get_all_prices(
    user=Depends(get_current_supabase_user),
    settings=Depends(get_settings_dependency),
):
    """Fetch live prices for all KSE-100 tickers from the PSX proxy."""
    _require_psx_proxy()
    return ApiResponse(
        message="PSX proxy is configured, but provider mapping is not implemented yet.",
        data={"provider": settings.PSX_PROXY_URL},
    )


@router.get(
    "/{ticker}",
    response_model=ApiResponse,
    responses={503: {"model": ServiceUnavailableResponse}},
    status_code=status.HTTP_200_OK,
)
async def get_price(
    ticker: str,
    user=Depends(get_current_supabase_user),
    settings=Depends(get_settings_dependency),
):
    """Fetch live price for a single PSX ticker from the PSX proxy."""
    _require_psx_proxy()
    return ApiResponse(
        message="PSX proxy is configured, but provider mapping is not implemented yet.",
        data={"ticker": ticker.upper(), "provider": settings.PSX_PROXY_URL},
    )
