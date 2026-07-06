"""Company profile and metrics endpoints — C1 through C8."""
from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_company_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_current_supabase_user, get_optional_user
from app.core.exceptions import ExternalServiceError
from app.services.company_service import CompanyService

router = APIRouter(tags=["companies"])


@router.get("/companies/{ticker}/overview", status_code=status.HTTP_200_OK)
async def get_company_overview(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C1 — Full company overview."""
    normalized = validate_ticker(ticker)
    overview, cache_hit, cache_age = await service.get_overview(normalized)
    return make_response(
        overview.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/profile", status_code=status.HTTP_200_OK)
async def get_company_profile_contract(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C2 — Company profile."""
    normalized = validate_ticker(ticker)
    profile = await service.get_profile(normalized)
    return make_response(profile.model_dump(mode="json"), provider="capital_stake")


@router.get("/companies/{ticker}/statistics", status_code=status.HTTP_200_OK)
async def get_company_statistics(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C3 — Key statistics with tier gating."""
    normalized = validate_ticker(ticker)
    stats, cache_hit, cache_age = await service.get_statistics(normalized, user)
    return make_response(
        stats.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/earnings", status_code=status.HTTP_200_OK)
async def get_company_earnings(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C4 — Earnings summary and chart."""
    normalized = validate_ticker(ticker)
    earnings, cache_hit, cache_age = await service.get_earnings(normalized)
    return make_response(
        earnings.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/dividends", status_code=status.HTTP_200_OK)
async def get_company_dividends(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C5 — Dividend summary."""
    normalized = validate_ticker(ticker)
    dividends, cache_hit, cache_age = await service.get_dividends(normalized)
    return make_response(
        dividends.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/ownership", status_code=status.HTTP_200_OK)
async def get_company_ownership(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C6 — Ownership breakdown."""
    normalized = validate_ticker(ticker)
    ownership, cache_hit, cache_age = await service.get_ownership(normalized)
    return make_response(
        ownership.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/period-returns", status_code=status.HTTP_200_OK)
async def get_company_period_returns(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C7 — Period return percentages."""
    normalized = validate_ticker(ticker)
    returns, cache_hit, cache_age = await service.get_period_returns(normalized)
    return make_response(
        returns.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/companies/{ticker}/faq", status_code=status.HTTP_200_OK)
async def get_company_faq(
    ticker: str = TickerPath(),
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_optional_user),
):
    """C8 — Auto-generated FAQ."""
    normalized = validate_ticker(ticker)
    faq, cache_hit, cache_age = await service.get_faq(normalized)
    return make_response(
        faq.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/company/{ticker}", status_code=status.HTTP_200_OK)
async def get_company_by_ticker(
    ticker: str,
    service: CompanyService = Depends(get_company_service),
    user=Depends(get_current_supabase_user),
):
    """Legacy company endpoint — requires auth."""
    if service.missing_config():
        raise ExternalServiceError(
            "Capital Stake",
            "Capital Stake is not configured.",
            error_code="SERVICE_UNAVAILABLE",
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
