"""Supabase JWT validation."""
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_supabase_token(
    credentials: HTTPAuthorizationCredentials | None,
    settings: Settings,
    *,
    optional: bool = False,
) -> dict[str, Any]:
    """Validate a Supabase JWT and return the payload."""
    if credentials is None:
        if optional:
            return {}
        if not settings.SUPABASE_JWT_SECRET and settings.is_development:
            return {"user_id": "development", "role": "authenticated"}
        raise AuthenticationError("Missing bearer token", error_code="TOKEN_MISSING")

    if not settings.SUPABASE_JWT_SECRET:
        if settings.is_development:
            return {"user_id": "development", "role": "authenticated"}
        raise AuthenticationError(
            "SUPABASE_JWT_SECRET is not configured",
            error_code="TOKEN_INVALID",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
    except ExpiredSignatureError as exc:
        logger.warning("Expired Supabase token")
        raise AuthenticationError(
            "Your session has expired. Please sign in again.",
            error_code="TOKEN_EXPIRED",
        ) from exc
    except JWTError as exc:
        logger.warning("Invalid Supabase token: %s", exc)
        raise AuthenticationError(
            "Invalid authentication credentials",
            error_code="TOKEN_INVALID",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError(
            "Invalid authentication credentials",
            error_code="TOKEN_INVALID",
        )
    return {"user_id": user_id, **payload}


def validate_supabase_token_query(token: str | None, settings: Settings) -> dict[str, Any]:
    """Validate JWT from SSE ?token= query param."""
    if not token:
        raise AuthenticationError("Missing token query parameter", error_code="TOKEN_MISSING")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return validate_supabase_token(creds, settings, optional=False)
