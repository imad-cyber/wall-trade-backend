"""AI-specific cache wrapper."""
from typing import Optional

from app.domain.analysis.models import AnalysisCache, AnalysisResult
from app.services.cache_service import CacheService


class AICache:
    def __init__(self, cache_service: CacheService):
        self._cache = cache_service

    def get(self, ticker: str) -> Optional[AnalysisCache]:
        return self._cache.get_analysis(ticker)

    def set(self, result: AnalysisResult) -> AnalysisCache:
        return self._cache.set_analysis(result)
