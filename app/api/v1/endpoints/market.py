"""Market data endpoints — M1 through M6."""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.v1.dependencies import get_market_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_optional_user
from app.auth.supabase_auth import validate_supabase_token_query
from app.core.config import get_settings
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_market_summary(
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """Market dashboard summary — indices and featured index chart."""
    summary, cache_hit, cache_age = await service.get_market_summary()
    return make_response(
        summary.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/quote/{ticker}", status_code=status.HTTP_200_OK)
async def get_market_quote(
    ticker: str = TickerPath(),
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """M1 — Live stock quote."""
    normalized = validate_ticker(ticker)
    quote, cache_hit, cache_age = await service.get_quote(normalized)
    return make_response(
        quote.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/ohlcv", status_code=status.HTTP_200_OK)
async def get_market_ohlcv(
    ticker: str = TickerPath(),
    range_: str = Query("2y", alias="range"),
    interval: str = Query("1d"),
    include_pre_post: bool = Query(False),
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """M2 — OHLCV price history."""
    normalized = validate_ticker(ticker)
    ohlcv, cache_hit, cache_age = await service.get_ohlcv(normalized, range_, interval)
    return make_response(
        ohlcv.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/peers", status_code=status.HTTP_200_OK)
async def get_market_peers(
    ticker: str = TickerPath(),
    category: str = Query("Value"),
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """M3 — Peer comparison metrics."""
    normalized = validate_ticker(ticker)
    peers, cache_hit, cache_age = await service.get_peers(normalized, category)
    return make_response(
        peers.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/related", status_code=status.HTTP_200_OK)
async def get_related_tickers(
    ticker: str = TickerPath(),
    limit: int = Query(5, ge=1, le=20),
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """M4 — People Also Watch."""
    normalized = validate_ticker(ticker)
    related, cache_hit, cache_age = await service.get_related(normalized, limit)
    return make_response(
        related.model_dump(mode="json"),
        cache_hit=cache_hit,
        provider="capital_stake",
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/{ticker}/opex-dates", status_code=status.HTTP_200_OK)
async def get_opex_dates(
    ticker: str = TickerPath(),
    service: MarketService = Depends(get_market_service),
    user=Depends(get_optional_user),
):
    """M5 — Options expiry dates."""
    normalized = validate_ticker(ticker)
    opex, cache_hit, cache_age = await service.get_opex_dates(normalized)
    return make_response(
        opex.model_dump(mode="json"),
        cache_hit=cache_hit,
        cache_age_seconds=cache_age if cache_hit else None,
    )


@router.get("/stream/quote/{ticker}")
async def stream_market_quote(
    ticker: str = TickerPath(),
    token: str | None = Query(None),
    service: MarketService = Depends(get_market_service),
):
    """M6 — SSE live quote stream."""
    settings = get_settings()
    if token:
        validate_supabase_token_query(token, settings)
    normalized = validate_ticker(ticker)
    return StreamingResponse(
        service.stream_quote(normalized),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
