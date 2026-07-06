"""Financial statement endpoints — F1, F2, F3."""
from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_financials_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_optional_user
from app.services.financials_service import FinancialsService

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/{ticker}/income-statement", status_code=status.HTTP_200_OK)
async def get_income_statement(
    ticker: str = TickerPath(),
    period: str = Query("annual"),
    years: int = Query(8, ge=1, le=20),
    service: FinancialsService = Depends(get_financials_service),
    user=Depends(get_optional_user),
):
    """F1 — Income statement."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_income_statement(normalized, period, years)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/balance-sheet", status_code=status.HTTP_200_OK)
async def get_balance_sheet(
    ticker: str = TickerPath(),
    period: str = Query("annual"),
    years: int = Query(8, ge=1, le=20),
    service: FinancialsService = Depends(get_financials_service),
    user=Depends(get_optional_user),
):
    """F2 — Balance sheet."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_balance_sheet(normalized, period, years)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/cash-flow", status_code=status.HTTP_200_OK)
async def get_cash_flow(
    ticker: str = TickerPath(),
    period: str = Query("annual"),
    years: int = Query(8, ge=1, le=20),
    service: FinancialsService = Depends(get_financials_service),
    user=Depends(get_optional_user),
):
    """F3 — Cash flow statement."""
    normalized = validate_ticker(ticker)
    result, cache_hit, cache_age = await service.get_cash_flow(normalized, period, years)
    return make_response(
        result.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )
