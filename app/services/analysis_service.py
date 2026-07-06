"""Contract analysis service — A1 through A5."""
from typing import Any, AsyncIterator, Optional

from app.ai.analysis_pipeline import AnalysisPipeline
from app.api.v1.schemas.analysis import (
    AnalystResponse,
    EarningsCallResponse,
    SwotResponse,
    TechnicalAnalysisResponse,
)
from app.core.config import get_settings
from app.domain.analysis.models import AnalysisCache
from app.providers.capital_stake.client import CapitalStakeClient
from app.providers.capital_stake.extended_mapper import (
    _rows_from_list,
    map_analyst,
    map_earnings_call,
    map_swot,
    map_technical,
)
from app.repositories.analysis_repository import AnalysisRepository
from app.services.cache_service import CacheService
from app.utils.tiering import get_user_tier

CACHE_ANALYST = 86400
CACHE_TECHNICAL = 900


class AnalysisService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        cache_service: CacheService,
        pipeline: Optional[AnalysisPipeline] = None,
        capital_stake: Optional[CapitalStakeClient] = None,
    ):
        self.analysis_repo = analysis_repo
        self.cache_service = cache_service
        self.pipeline = pipeline
        self.capital_stake = capital_stake or CapitalStakeClient()
        self.settings = get_settings()
        self._memory = __import__("app.core.memory_cache", fromlist=["get_memory_cache"]).get_memory_cache()

    def get_cached_analysis(self, ticker: str) -> Optional[AnalysisCache]:
        return self.cache_service.get_analysis(ticker)

    def missing_config(self) -> list[str]:
        missing = []
        if not self.settings.ai_api_key:
            missing.append("AI_API_KEY or OPENAI_API_KEY")
        if not self.settings.capital_stake_key:
            missing.append("CAPITAL_STAKE_API_KEY or CAPITAL_API_KEY")
        return missing

    async def stream_analysis(self, ticker: str, *, refresh: bool = False) -> AsyncIterator[str]:
        if self.pipeline is None:
            yield "event: status\ndata: Analysis pipeline is not configured.\n\n"
            yield "data: [DONE]\n\n"
            return
        async for event in self.pipeline.run(ticker, refresh=refresh):
            yield event

    def create_cache_row(self, payload: dict) -> dict:
        return self.analysis_repo.create_cache_row(payload)

    async def get_analyst_ratings(
        self, ticker: str, page: int = 1, limit: int = 10,
    ) -> tuple[AnalystResponse, bool, int]:
        cache_key = f"analysis:analyst:{ticker.upper()}:{page}:{limit}"
        cached = self._memory.get(cache_key)
        if cached:
            return cached[0], True, cached[1]

        quote = await self.capital_stake.get_stock_quote(ticker)
        ratings_raw: list[dict] = []
        try:
            rows = self.analysis_repo.list(limit=100, filters={"ticker": ticker.upper()})
            ratings_raw = rows
        except Exception:
            ratings_raw = []

        result = map_analyst(ticker, ratings_raw, page, limit, quote.price)
        self._memory.set(cache_key, result, CACHE_ANALYST)
        return result, False, 0

    async def get_swot(self, ticker: str) -> tuple[SwotResponse, bool]:
        cached_row = self.analysis_repo.get_valid_cache(ticker)
        if cached_row:
            raw = cached_row.to_db_payload().get("analysis", {})
            items = raw.get("swot_items", []) if isinstance(raw, dict) else []
            if items:
                return map_swot(ticker, items), True
        from app.providers.capital_stake.mapper import _iso_timestamp
        return SwotResponse(ticker=ticker.upper(), generated_at=_iso_timestamp(None), items=[]), False

    async def get_technical(
        self, ticker: str, user: Optional[dict[str, Any]] = None,
    ) -> tuple[TechnicalAnalysisResponse, bool, int]:
        tier = get_user_tier(user)
        cache_key = f"analysis:technical:{ticker.upper()}:{tier}"
        cached = self._memory.get(cache_key)
        if cached:
            return cached[0], True, cached[1]

        raw: dict = {}
        try:
            raw = self.capital_stake._unwrap_data(await self.capital_stake.get_technicals(ticker))
        except Exception:
            raw = {}
        result = map_technical(ticker, raw, tier=tier)
        self._memory.set(cache_key, result, CACHE_TECHNICAL)
        return result, False, 0

    async def get_earnings_call(self, ticker: str) -> EarningsCallResponse:
        try:
            news = self.capital_stake._unwrap_data(await self.capital_stake.get_company_news(ticker))
            articles = _rows_from_list(news)
            earnings_articles = [a for a in articles if "earnings" in str(a.get("headline", "")).lower()]
            if earnings_articles:
                return map_earnings_call(ticker, earnings_articles[0])
        except Exception:
            pass
        return map_earnings_call(ticker, {})

    async def get_scorecard(self, ticker: str, user_id: str) -> dict:
        return {"ticker": ticker.upper(), "user_id": user_id}
