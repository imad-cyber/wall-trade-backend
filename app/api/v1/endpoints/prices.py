"""Live price endpoints via PSX proxy."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import get_market_service
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_current_supabase_user
from app.services.market_service import MarketService

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_prices(
    service: MarketService = Depends(get_market_service),
    user=Depends(get_current_supabase_user),
):
    missing = service.missing_config()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "errors": [{"code": "SERVICE_UNAVAILABLE", "message": "PSX proxy is not configured."}],
                "missing_configuration": missing,
            },
        )
    prices = await service.get_all_prices()
    return make_response([p.model_dump(mode="json") for p in prices])


@router.get("/{ticker}", status_code=status.HTTP_200_OK)
async def get_price(
    ticker: str,
    service: MarketService = Depends(get_market_service),
    user=Depends(get_current_supabase_user),
):
    missing = service.missing_config()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "success": False,
                "errors": [{"code": "SERVICE_UNAVAILABLE", "message": "PSX proxy is not configured."}],
                "missing_configuration": missing,
            },
        )
    price = await service.get_price(ticker)
    return make_response(price.model_dump(mode="json"))
