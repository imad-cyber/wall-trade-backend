"""Application lifespan — startup and shutdown hooks."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.providers.supabase.client import get_supabase_client, close_supabase_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    get_settings.cache_clear()
    settings = get_settings()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.ENVIRONMENT)
    logger.info("Capital Stake API base: %s", settings.capital_stake_base_url)

    scheduler = None
    http_clients: list = []

    try:
        from app.core.http import close_http_clients

        await close_http_clients()
    except Exception:
        pass

    try:
        get_supabase_client()
        logger.info("Supabase client initialized")
    except Exception as exc:
        logger.error("Failed to initialize Supabase: %s", exc)
        if settings.is_production:
            raise

    try:
        from app.core.http import get_http_client_registry

        registry = get_http_client_registry()
        http_clients = list(registry.values())
    except Exception:
        pass

    try:
        from app.tasks import start_scheduler

        scheduler = start_scheduler()
        if scheduler:
            logger.info("Background task scheduler started")
    except Exception as exc:
        logger.warning("Scheduler not started: %s", exc)

    app.state.scheduler = scheduler
    app.state.http_clients = http_clients

    yield

    logger.info("Shutting down application")
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception as exc:
            logger.warning("Scheduler shutdown error: %s", exc)

    try:
        from app.core.http import close_http_clients

        await close_http_clients()
    except Exception:
        pass

    close_supabase_client()
