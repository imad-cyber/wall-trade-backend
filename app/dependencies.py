"""Application-level dependencies (DB, settings)."""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.jwt import security
from app.core.config import Settings, get_settings
from app.providers.supabase.client import get_authed_client, get_supabase_client


def get_settings_dependency() -> Settings:
    return get_settings()


async def get_db_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Generator:
    """Yield Supabase client — authed when bearer token present."""
    if credentials is not None:
        settings = get_settings()
        if not settings.SUPABASE_URL or not settings.supabase_database_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase URL/key are not configured",
            )
        yield get_authed_client(credentials.credentials)
        return
    yield get_supabase_client()


async def verify_environment() -> bool:
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.supabase_database_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application not properly configured",
        )
    return True
