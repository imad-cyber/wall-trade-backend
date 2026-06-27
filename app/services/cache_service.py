"""Analysis cache service with TTL management."""
from typing import Optional

from app.core.config import get_settings
from app.domain.analysis.models import AnalysisCache, AnalysisResult
from app.observability.metrics import record_cache_hit
from app.repositories.analysis_repository import AnalysisRepository


class CacheService:
    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo
        self.settings = get_settings()

    def get_analysis(self, ticker: str) -> Optional[AnalysisCache]:
        cache = self.analysis_repo.get_valid_cache(ticker)
        if cache:
            record_cache_hit("analysis")
        return cache

    def set_analysis(self, result: AnalysisResult) -> AnalysisCache:
        cache = AnalysisCache(ticker=result.ticker, result=result)
        return self.analysis_repo.upsert_cache(cache)
