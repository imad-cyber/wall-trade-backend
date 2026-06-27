"""FastAPI auth dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.jwt import AuthService, security
from app.auth.supabase_auth import validate_supabase_token
from app.core.config import Settings, get_settings


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from application JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service = AuthService()
    payload = auth_service.verify_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"user_id": user_id, **payload}


async def get_current_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Validate Supabase JWT for protected Wall-Trade endpoints."""
    if not settings.SUPABASE_JWT_SECRET and settings.is_development:
        return {"user_id": "development", "role": "authenticated"}
    return validate_supabase_token(credentials, settings)
