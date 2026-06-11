"""
API v1 router setup.
Combines all v1 endpoints into a single router.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    analysis,
    companies,
    health,
    macro,
    market_feel,
    portfolios,
    prices,
    script_history,
    sector_feel,
    trades,
)

# Create the main API router for v1 endpoints. Prefixes are applied in app.api.
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(companies.router)
api_router.include_router(macro.router)
api_router.include_router(prices.router)
api_router.include_router(analysis.router)
api_router.include_router(portfolios.router)
api_router.include_router(trades.router)
api_router.include_router(market_feel.router)
api_router.include_router(sector_feel.router)
api_router.include_router(script_history.router)
api_router.include_router(health.router)

__all__ = ["api_router"]
