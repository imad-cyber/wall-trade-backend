"""Domain model unit tests."""
from datetime import datetime, timezone

from app.domain.analysis.models import AnalysisCache, AnalysisResult
from app.domain.company.models import CompanyProfile
from app.domain.market.models import Price
from app.domain.macro.models import MacroCache


class TestDomainModels:
    def test_company_profile_from_provider_row(self):
        profile = CompanyProfile.from_provider_row("ENGRO", {"name": "Engro Corp", "pe": 12.5})
        assert profile.ticker == "ENGRO"
        assert profile.name == "Engro Corp"

    def test_price_from_provider_row(self):
        price = Price.from_provider_row({"ticker": "hbl", "price": 150.5})
        assert price.ticker == "HBL"
        assert float(price.price) == 150.5

    def test_analysis_cache_from_db_row(self):
        now = datetime.now(timezone.utc).isoformat()
        row = {
            "id": 1,
            "ticker": "ENGRO",
            "verdict": "BUY",
            "summary": "Strong",
            "analysis": {"verdict": "BUY", "summary": "Strong", "sentiment": "bullish"},
            "generated_at": now,
            "expires_at": now,
        }
        cache = AnalysisCache.from_db_row(row)
        assert cache.ticker == "ENGRO"
        assert cache.result.verdict == "BUY"

    def test_macro_cache_from_db_row(self):
        row = {"id": 1, "data": {"inflation": 8.5}, "updated_at": "2026-01-01T00:00:00+00:00"}
        macro = MacroCache.from_db_row(row)
        assert macro.id == 1
