"""Crypto market data endpoints — CoinGecko API proxy."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_crypto_service
from app.api.v1.schemas.envelope import make_response
from app.auth.dependencies import get_optional_user
from app.services.crypto_service import CryptoService

router = APIRouter(prefix="/crypto", tags=["crypto"])


def _crypto_response(
    data: Any,
    *,
    cache_hit: bool,
    cache_age: int,
) -> dict[str, Any]:
    return make_response(
        data,
        cache_hit=cache_hit,
        provider="coingecko",
        cache_age_seconds=cache_age if cache_hit else None,
    ).model_dump()


@router.get("/ping", status_code=status.HTTP_200_OK)
async def crypto_ping(
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """CoinGecko API health check."""
    data, cache_hit, cache_age = await service.ping()
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/key", status_code=status.HTTP_200_OK)
async def crypto_api_key_usage(
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """CoinGecko API key usage and rate-limit status."""
    data, cache_hit, cache_age = await service.get_api_key_usage()
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/price", status_code=status.HTTP_200_OK)
async def crypto_simple_price(
    ids: Optional[str] = Query(None, description="Comma-separated coin IDs, e.g. bitcoin,ethereum"),
    names: Optional[str] = Query(None, description="Comma-separated coin names"),
    symbols: Optional[str] = Query(None, description="Comma-separated coin symbols"),
    vs_currencies: str = Query("usd", description="Target currencies, e.g. usd,eur"),
    include_market_cap: bool = Query(False),
    include_24hr_vol: bool = Query(False),
    include_24hr_change: bool = Query(False),
    include_last_updated_at: bool = Query(False),
    precision: Optional[str] = Query(None),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Simple coin prices by ID, name, or symbol."""
    data, cache_hit, cache_age = await service.get_simple_price(
        ids=ids,
        names=names,
        symbols=symbols,
        vs_currencies=vs_currencies,
        include_market_cap=include_market_cap,
        include_24hr_vol=include_24hr_vol,
        include_24hr_change=include_24hr_change,
        include_last_updated_at=include_last_updated_at,
        precision=precision,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/markets", status_code=status.HTTP_200_OK)
async def crypto_markets(
    vs_currency: str = Query("usd"),
    ids: Optional[str] = Query(None, description="Filter by comma-separated coin IDs"),
    category: Optional[str] = Query(None),
    order: str = Query("market_cap_desc"),
    per_page: int = Query(100, ge=1, le=250),
    page: int = Query(1, ge=1),
    sparkline: bool = Query(False),
    price_change_percentage: Optional[str] = Query(None, description="e.g. 1h,24h,7d"),
    locale: str = Query("en"),
    precision: Optional[str] = Query(None),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Coin market data with ranking, sparklines, and ATH/ATL."""
    data, cache_hit, cache_age = await service.get_coins_markets(
        vs_currency=vs_currency,
        ids=ids,
        category=category,
        order=order,
        per_page=per_page,
        page=page,
        sparkline=sparkline,
        price_change_percentage=price_change_percentage,
        locale=locale,
        precision=precision,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/coins/{coin_id}", status_code=status.HTTP_200_OK)
async def crypto_coin_detail(
    coin_id: str,
    localization: bool = Query(False),
    tickers: bool = Query(False),
    market_data: bool = Query(True),
    community_data: bool = Query(False),
    developer_data: bool = Query(False),
    sparkline: bool = Query(False),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Detailed coin metadata and market data."""
    data, cache_hit, cache_age = await service.get_coin_detail(
        coin_id,
        localization=localization,
        tickers=tickers,
        market_data=market_data,
        community_data=community_data,
        developer_data=developer_data,
        sparkline=sparkline,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/coins/{coin_id}/market-chart", status_code=status.HTTP_200_OK)
async def crypto_market_chart(
    coin_id: str,
    vs_currency: str = Query("usd"),
    days: str = Query("30", description="1, 7, 14, 30, 90, 180, 365, or max"),
    interval: Optional[str] = Query(None, description="daily or hourly override"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Historical price, market cap, and volume chart data."""
    data, cache_hit, cache_age = await service.get_market_chart(
        coin_id,
        vs_currency=vs_currency,
        days=days,
        interval=interval,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/coins/{coin_id}/market-chart/range", status_code=status.HTTP_200_OK)
async def crypto_market_chart_range(
    coin_id: str,
    vs_currency: str = Query("usd"),
    from_timestamp: int = Query(..., alias="from", description="UNIX timestamp (seconds)"),
    to_timestamp: int = Query(..., alias="to", description="UNIX timestamp (seconds)"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Historical chart data within a UNIX timestamp range."""
    data, cache_hit, cache_age = await service.get_market_chart_range(
        coin_id,
        vs_currency=vs_currency,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/coins/{coin_id}/ohlc", status_code=status.HTTP_200_OK)
async def crypto_ohlc(
    coin_id: str,
    vs_currency: str = Query("usd"),
    days: str = Query("30", description="1, 7, 14, 30, 90, or 180"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """OHLC candlestick data for a coin."""
    data, cache_hit, cache_age = await service.get_ohlc(
        coin_id,
        vs_currency=vs_currency,
        days=days,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/trending", status_code=status.HTTP_200_OK)
async def crypto_trending(
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Trending coins, NFTs, and categories from the last 24 hours."""
    data, cache_hit, cache_age = await service.get_trending()
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/top-gainers-losers", status_code=status.HTTP_200_OK)
async def crypto_top_gainers_losers(
    vs_currency: str = Query("usd"),
    duration: str = Query("24h", description="1h, 24h, 7d, 14d, 30d, 60d, or 1y"),
    price_change_percentage: Optional[str] = Query(None),
    top_coins: Optional[str] = Query(None, description="300, 500, 1000, or all"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Top 30 gainers and losers by price change."""
    data, cache_hit, cache_age = await service.get_top_gainers_losers(
        vs_currency=vs_currency,
        duration=duration,
        price_change_percentage=price_change_percentage,
        top_coins=top_coins,
    )
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/search", status_code=status.HTTP_200_OK)
async def crypto_search(
    query: str = Query(..., min_length=1, description="Search by name or symbol"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """Search coins, exchanges, categories, and NFTs by name or symbol."""
    data, cache_hit, cache_age = await service.search(query)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get(
    "/onchain/networks/{network}/token-price/{address}",
    status_code=status.HTTP_200_OK,
)
async def crypto_onchain_token_price(
    network: str,
    address: str,
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — on-chain token price by contract address."""
    data, cache_hit, cache_age = await service.get_onchain_token_price(network, address)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get(
    "/onchain/networks/{network}/pools/{address}",
    status_code=status.HTTP_200_OK,
)
async def crypto_onchain_pool(
    network: str,
    address: str,
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — DEX pool data by address."""
    data, cache_hit, cache_age = await service.get_onchain_pool(network, address)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/onchain/trending-pools", status_code=status.HTTP_200_OK)
async def crypto_onchain_trending_pools(
    network: Optional[str] = Query(None, description="Optional network slug, e.g. eth"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — trending on-chain pools."""
    data, cache_hit, cache_age = await service.get_onchain_trending_pools(network)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/onchain/new-pools", status_code=status.HTTP_200_OK)
async def crypto_onchain_new_pools(
    network: Optional[str] = Query(None, description="Optional network slug, e.g. eth"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — newly created on-chain pools."""
    data, cache_hit, cache_age = await service.get_onchain_new_pools(network)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get("/onchain/pools/megafilter", status_code=status.HTTP_200_OK)
async def crypto_onchain_megafilter(
    sort: str = Query("pool_created_at_desc"),
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — pool screener with sort and filter options."""
    data, cache_hit, cache_age = await service.get_onchain_megafilter(sort=sort)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get(
    "/onchain/networks/{network}/tokens/{address}/info",
    status_code=status.HTTP_200_OK,
)
async def crypto_onchain_token_info(
    network: str,
    address: str,
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — token security info and GT score."""
    data, cache_hit, cache_age = await service.get_onchain_token_info(network, address)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)


@router.get(
    "/onchain/networks/{network}/tokens/{address}/top-holders",
    status_code=status.HTTP_200_OK,
)
async def crypto_onchain_token_top_holders(
    network: str,
    address: str,
    service: CryptoService = Depends(get_crypto_service),
    user=Depends(get_optional_user),
):
    """GeckoTerminal — top token holders."""
    data, cache_hit, cache_age = await service.get_onchain_token_top_holders(network, address)
    return _crypto_response(data, cache_hit=cache_hit, cache_age=cache_age)
