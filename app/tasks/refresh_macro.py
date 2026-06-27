"""Refresh macro cache from FMP provider."""
from app.core.logging import get_logger

logger = get_logger(__name__)


async def refresh_macro() -> None:
    logger.info("Background task: refresh_macro started")
    try:
        from app.providers.fmp.client import FMPClient
        from app.core.config import get_settings

        settings = get_settings()
        if not settings.FMP_API_KEY:
            logger.debug("FMP_API_KEY not set — skipping macro refresh")
            return
        client = FMPClient()
        await client.get_macro_indicators()
        logger.info("Macro data refreshed from FMP")
    except Exception as exc:
        logger.warning("Macro refresh failed: %s", exc)
