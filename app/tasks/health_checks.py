"""Periodic health checks for external dependencies."""
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)


async def health_checks() -> None:
    settings = get_settings()
    checks = {
        "supabase": bool(settings.SUPABASE_URL and settings.supabase_database_key),
        "capital_stake": bool(settings.capital_stake_key),
        "psx_proxy": bool(settings.psx_proxy_base_url),
        "ai": bool(settings.ai_api_key),
        "fmp": bool(settings.FMP_API_KEY),
    }
    unhealthy = [k for k, v in checks.items() if not v]
    if unhealthy:
        logger.debug("Health check — unconfigured: %s", unhealthy)
    else:
        logger.debug("Health check — all integrations configured")
