"""Narrative intelligence service — NI1 through NI13."""
import asyncio
import json
from typing import Any, AsyncIterator, Optional

from app.api.v1.schemas.narrative import (
    HeroStatsResponse,
    InfluenceNetworkResponse,
    NarrativeTickerListResponse,
    NarrativeTimelineResponse,
    UnifiedTickerNarrativeResponse,
)
from app.core.memory_cache import get_memory_cache
from app.repositories.narrative_repository import NarrativeRepository
from app.services.company_service import CompanyService
from app.services.market_service import MarketService

CACHE_TTL = 300


class NarrativeService:
    def __init__(
        self,
        repo: NarrativeRepository,
        market_service: MarketService,
        company_service: CompanyService,
    ):
        self.repo = repo
        self.market = market_service
        self.company = company_service
        self._cache = get_memory_cache()

    def _cached(self, key: str, factory):
        cached = self._cache.get(key)
        if cached:
            return cached[0]
        result = factory()
        self._cache.set(key, result, CACHE_TTL)
        return result

    def get_tracked_tickers(self) -> NarrativeTickerListResponse:
        def factory():
            tickers = self.repo.get_tickers()
            return NarrativeTickerListResponse(tickers=tickers, count=len(tickers))
        return self._cached("narrative:tickers", factory)

    def get_unified(self, ticker: str) -> UnifiedTickerNarrativeResponse:
        def factory():
            row = self.repo.get_unified(ticker)
            return UnifiedTickerNarrativeResponse(ticker=ticker.upper(), data=row or {})
        return self._cached(f"narrative:unified:{ticker.upper()}", factory)

    def get_trending(self, limit: int = 8) -> list[dict[str, Any]]:
        return self._cached(f"narrative:trending:{limit}", lambda: self.repo.get_trending(limit))

    def get_traps(self, limit: int = 20, verdict: str = "all") -> list[dict[str, Any]]:
        return self._cached(
            f"narrative:traps:{limit}:{verdict}",
            lambda: self.repo.get_traps(limit, verdict),
        )

    def get_coordination(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._cached(f"narrative:coordination:{limit}", lambda: self.repo.get_coordination(limit))

    def get_ecosystem_tickers(self) -> list[dict[str, Any]]:
        return self._cached("narrative:ecosystem:tickers", self.repo.get_ecosystem_tickers)

    def get_ecosystem_themes(self) -> list[dict[str, Any]]:
        return self._cached("narrative:ecosystem:themes", self.repo.get_ecosystem_themes)

    def get_network(self) -> InfluenceNetworkResponse:
        def factory():
            nodes, edges = self.repo.get_network()
            return InfluenceNetworkResponse(nodes=nodes, edges=edges)
        return self._cached("narrative:network", factory)

    def get_hero_stats(self) -> HeroStatsResponse:
        def factory():
            stats = self.repo.get_hero_stats()
            return HeroStatsResponse(**stats)
        return self._cached("narrative:hero-stats", factory)

    def get_dying(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._cached(f"narrative:dying:{limit}", lambda: self.repo.get_dying(limit))

    def get_scorecard(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._cached(f"narrative:scorecard:{limit}", lambda: self.repo.get_scorecard(limit))

    async def get_timeline(self, ticker: str) -> NarrativeTimelineResponse:
        stories = self.repo.get_timeline_stories(ticker)
        ohlcv, _, _ = await self.market.get_ohlcv(ticker, "2y", "1d")
        opex, _, _ = await self.market.get_opex_dates(ticker)
        price_history = [p.model_dump() for p in ohlcv.points]

        earnings_list: list[dict[str, Any]] = []
        try:
            earnings_resp, _, _ = await self.company.get_earnings(ticker)
            earnings_list = [point.model_dump(mode="json") for point in earnings_resp.chart]
        except Exception:
            pass

        return NarrativeTimelineResponse(
            ticker=ticker.upper(),
            stories=stories,
            earnings=earnings_list,
            opex_dates=opex.opex_dates,
            price_history=price_history,
        )

    async def stream_updates(self, user_id: str) -> AsyncIterator[str]:
        elapsed = 0
        try:
            while True:
                yield ": ping\n\n"
                payload = {"type": "heartbeat", "user_id": user_id}
                yield f"event: narrative_update\ndata: {json.dumps(payload)}\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            yield f"event: stream_end\ndata: {json.dumps({'reason': 'client_disconnect'})}\n\n"
