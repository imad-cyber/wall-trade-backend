"""Application dependencies for dependency injection."""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from supabase import create_client

from app.auth import security
from app.database import get_db_client
from app.config import get_settings


async def get_settings_dependency():
    """
    Dependency to get application settings.
    
    Returns:
        Settings: Application settings instance
    """
    return get_settings()


async def get_db_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Generator:
    """
    Dependency to get a Supabase client.

    When a frontend Supabase JWT is supplied, pass it through to PostgREST so
    authenticated RLS policies are evaluated for the current user. Without a
    bearer token, the shared anon/publishable-key client is used.

    Yields:
        Client: Database client instance
    """
    if credentials is not None:
        settings = get_settings()
        supabase_key = settings.supabase_database_key
        if not settings.SUPABASE_URL or not supabase_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase URL/key are not configured",
            )
        db = create_client(settings.SUPABASE_URL, supabase_key)
        db.postgrest.auth(credentials.credentials)
        yield db
        return

    db = get_db_client()
    yield db


async def verify_environment():
    """
    Verify application environment is properly configured.
    
    Raises:
        HTTPException: If environment is not properly configured
    """
    settings = get_settings()
    if not settings.SUPABASE_URL or not settings.supabase_database_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application not properly configured",
        )
    return True
