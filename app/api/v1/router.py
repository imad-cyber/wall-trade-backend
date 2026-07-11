"""
API v1 router setup.
Combines all v1 endpoints into a single router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    ai,
    alerts,
    analysis,
    analysis_contract,
    companies,
    crypto,
    financials,
    health,
    macro,
    market,
    market_feel,
    narrative,
    news,
    portfolios,
    prices,
    reports,
    script_history,
    search,
    sector_feel,
    trades,
    users,
    watchlist,
)

api_router = APIRouter()

# Contract-compliant endpoints (API_SPECIFICATION.md)
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(market.router)
api_router.include_router(companies.router)
api_router.include_router(analysis_contract.router)
api_router.include_router(financials.router)
api_router.include_router(news.router)
api_router.include_router(watchlist.router)
api_router.include_router(search.router)
api_router.include_router(crypto.router)
api_router.include_router(reports.router)
api_router.include_router(narrative.router)
api_router.include_router(ai.router)
api_router.include_router(alerts.router)

# Legacy MVP endpoints (retained for backward compatibility)
api_router.include_router(macro.router)
api_router.include_router(prices.router)
api_router.include_router(analysis.router)
api_router.include_router(portfolios.router)
api_router.include_router(trades.router)
api_router.include_router(market_feel.router)
api_router.include_router(sector_feel.router)
api_router.include_router(script_history.router)

__all__ = ["api_router"]
