"""Core infrastructure unit tests."""
from app.core.config import get_settings
from app.core.exceptions import AIProviderError, RateLimitError


class TestCoreConfig:
    def test_get_settings_singleton(self):
        assert get_settings() is get_settings()

    def test_new_settings_fields(self):
        settings = get_settings()
        assert settings.AI_MODEL == "gpt-4o"
        assert settings.ANALYSIS_CACHE_TTL_HOURS == 24
        assert settings.DEFAULT_MAX_RETRIES == 3


class TestCoreExceptions:
    def test_ai_provider_error_status(self):
        exc = AIProviderError("fail")
        assert exc.status_code == 502

    def test_rate_limit_error_status(self):
        exc = RateLimitError()
        assert exc.status_code == 429
