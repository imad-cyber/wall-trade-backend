"""Clean expired analysis cache entries."""
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.providers.supabase.client import get_supabase_client

logger = get_logger(__name__)


async def cleanup_cache() -> None:
    logger.info("Background task: cleanup_cache started")
    try:
        client = get_supabase_client()
        now = datetime.now(timezone.utc).isoformat()
        client.table("analysis_cache").delete().lt("expires_at", now).execute()
        logger.info("Expired analysis cache entries cleaned")
    except Exception as exc:
        logger.warning("Cache cleanup failed: %s", exc)
