"""Warm frequently accessed cache entries."""
from app.core.logging import get_logger

logger = get_logger(__name__)

WARM_TICKERS = ["ENGRO", "HBL", "OGDC", "LUCK", "PSO"]


async def warm_cache() -> None:
    logger.info("Background task: warm_cache started for %s", WARM_TICKERS)
    try:
        from app.repositories.analysis_repository import AnalysisRepository
        from app.providers.supabase.client import get_supabase_client

        repo = AnalysisRepository(get_supabase_client())
        for ticker in WARM_TICKERS:
            cache = repo.get_valid_cache(ticker)
            if cache:
                logger.debug("Cache warm hit for %s", ticker)
    except Exception as exc:
        logger.warning("Cache warm failed: %s", exc)
