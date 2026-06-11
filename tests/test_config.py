"""
Tests for configuration settings.
"""
import pytest
from app.config import get_settings


class TestSettings:
    """Test settings configuration."""

    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = get_settings()
        
        assert settings.APP_NAME == "Wall-Trade-Backend"
        assert settings.DEBUG is False
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    def test_settings_environment_property(self):
        """Test is_development and is_production properties."""
        settings = get_settings()
        
        # Should be development by default (or as set in .env)
        assert hasattr(settings, "is_development")
        assert hasattr(settings, "is_production")
