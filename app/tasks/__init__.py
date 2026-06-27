"""Background task scheduler and jobs."""
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.tasks.cleanup_cache import cleanup_cache
from app.tasks.health_checks import health_checks
from app.tasks.refresh_macro import refresh_macro
from app.tasks.warm_cache import warm_cache

logger = get_logger(__name__)
_scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler() -> Optional[AsyncIOScheduler]:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(refresh_macro, "interval", hours=6, id="refresh_macro")
    _scheduler.add_job(cleanup_cache, "cron", hour=0, id="cleanup_cache")
    _scheduler.add_job(warm_cache, "interval", hours=12, id="warm_cache")
    _scheduler.add_job(health_checks, "interval", minutes=5, id="health_checks")
    _scheduler.start()
    logger.info("Registered %d background tasks", len(_scheduler.get_jobs()))
    return _scheduler


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return _scheduler
