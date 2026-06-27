"""AI analysis service."""
from typing import AsyncIterator, Optional

from app.ai.analysis_pipeline import AnalysisPipeline
from app.core.config import get_settings
from app.domain.analysis.models import AnalysisCache
from app.repositories.analysis_repository import AnalysisRepository
from app.services.cache_service import CacheService


class AnalysisService:
    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        cache_service: CacheService,
        pipeline: Optional[AnalysisPipeline] = None,
    ):
        self.analysis_repo = analysis_repo
        self.cache_service = cache_service
        self.pipeline = pipeline
        self.settings = get_settings()

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
