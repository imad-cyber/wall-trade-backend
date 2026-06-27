"""Supabase client lifecycle management."""
from typing import Optional

from supabase import Client, create_client

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return singleton Supabase client (service-role / anon key)."""
    global _client
    if _client is None:
        settings = get_settings()
        supabase_key = settings.supabase_database_key
        if not settings.SUPABASE_URL or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and one of SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY, "
                "or SUPABASE_ANON_KEY must be configured"
            )
        _client = create_client(settings.SUPABASE_URL, supabase_key)
        logger.info("Supabase client initialized")
    return _client


def get_authed_client(jwt_token: str) -> Client:
    """Return a client scoped with the user's JWT for RLS evaluation."""
    client = get_supabase_client()
    client.postgrest.auth(jwt_token)
    return client


def close_supabase_client() -> None:
    """Reset singleton on shutdown."""
    global _client
    if _client is not None:
        logger.info("Closing Supabase client")
        _client = None
