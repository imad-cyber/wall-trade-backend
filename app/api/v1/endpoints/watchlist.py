"""Watchlist endpoints — W1 through W4."""
from fastapi import APIRouter, Depends, status

from app.api.v1.dependencies import get_watchlist_service
from app.api.v1.schemas.envelope import make_response
from app.api.v1.schemas.watchlist import WatchlistAddRequest, WatchlistReorderRequest
from app.api.v1.validators import TickerPath, validate_ticker
from app.auth.dependencies import get_current_supabase_user
from app.services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_watchlist(
    user=Depends(get_current_supabase_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """W1 — User watchlist with live prices."""
    items = await service.get_watchlist(user["user_id"])
    return make_response([i.model_dump(mode="json") for i in items])


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    user=Depends(get_current_supabase_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """W2 — Add ticker to watchlist."""
    ticker = validate_ticker(body.ticker)
    item = await service.add_to_watchlist(user["user_id"], ticker)
    return make_response(item.model_dump(mode="json"))


@router.delete("/{ticker}", status_code=status.HTTP_200_OK)
async def remove_from_watchlist(
    ticker: str = TickerPath(),
    user=Depends(get_current_supabase_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """W3 — Remove ticker from watchlist."""
    normalized = validate_ticker(ticker)
    removed = await service.remove_from_watchlist(user["user_id"], normalized)
    return make_response({"removed": removed})


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_watchlist(
    body: WatchlistReorderRequest,
    user=Depends(get_current_supabase_user),
    service: WatchlistService = Depends(get_watchlist_service),
):
    """W4 — Reorder watchlist."""
    tickers = [validate_ticker(t) for t in body.tickers]
    items = await service.reorder(user["user_id"], tickers)
    return make_response([i.model_dump(mode="json") for i in items])
