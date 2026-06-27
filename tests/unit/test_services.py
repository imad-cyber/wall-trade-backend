"""Service layer unit tests."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.domain.analysis.models import AnalysisCache, AnalysisResult
from app.domain.analysis.enums import Sentiment
from app.repositories.analysis_repository import AnalysisRepository
from app.services.cache_service import CacheService


class TestCacheService:
    def test_cache_hit(self):
        repo = MagicMock(spec=AnalysisRepository)
        now = datetime.now(timezone.utc)
        cache = AnalysisCache(
            ticker="ENGRO",
            result=AnalysisResult(
                ticker="ENGRO",
                summary="s",
                verdict="HOLD",
                sentiment=Sentiment.NEUTRAL,
                generated_at=now,
                expires_at=now + timedelta(hours=24),
            ),
        )
        repo.get_valid_cache.return_value = cache
        service = CacheService(repo)
        result = service.get_analysis("ENGRO")
        assert result is not None
        assert result.ticker == "ENGRO"

    def test_cache_miss(self):
        repo = MagicMock(spec=AnalysisRepository)
        repo.get_valid_cache.return_value = None
        service = CacheService(repo)
        assert service.get_analysis("ENGRO") is None
