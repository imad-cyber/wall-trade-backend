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
    logger.info("CORS allowed_origins: %s", settings.allowed_origins)
    logger.info("CORS_ORIGIN_REGEX: %s", settings.CORS_ORIGIN_REGEX)
    logger.info(
        "Capital Stake token configured: %s",
        bool(settings.capital_stake_token),
    )
    if not settings.capital_stake_token:
        logger.error(
            "CRITICAL: No Capital Stake token configured — "
            "all market data requests will fail with AUTH_ERROR"
        )
    logger.info("CoinGecko API base: %s", settings.coingecko_base_url)
    logger.info(
        "CoinGecko API key configured: %s (plan=%s)",
        bool(settings.COINGECKO_API_KEY),
        settings.COINGECKO_PLAN,
    )
    if settings.SUPABASE_JWT_SECRET:
        logger.info("Supabase JWT validation: HS256 secret configured")
    elif settings.SUPABASE_URL:
        logger.info(
            "Supabase JWT validation: JWKS (asymmetric) via %s",
            settings.SUPABASE_URL.rstrip("/") + "/auth/v1/.well-known/jwks.json",
        )
    else:
        logger.warning("Supabase JWT validation: not configured")

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
