"""FastAPI auth dependencies."""
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import AuthService, security
from app.auth.supabase_auth import validate_supabase_token
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError

optional_bearer = HTTPBearer(auto_error=False)


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


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    settings: Settings = Depends(get_settings),
) -> Optional[dict[str, Any]]:
    """Return authenticated user payload or None for public/tiered routes."""
    if credentials is None:
        return None
    try:
        return validate_supabase_token(credentials, settings, optional=False)
    except AuthenticationError:
        # Invalid/expired token on optional routes → treat as anonymous
        return None


async def get_current_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Validate Supabase JWT for protected Wall-Trade endpoints."""
    has_auth_config = bool(settings.SUPABASE_JWT_SECRET or settings.SUPABASE_URL)
    if not has_auth_config:
        if settings.is_development:
            return {"user_id": "development", "role": "authenticated"}
        raise AuthenticationError(
            "Authentication is not configured",
            error_code="TOKEN_INVALID",
        )
    return validate_supabase_token(credentials, settings, optional=False)
