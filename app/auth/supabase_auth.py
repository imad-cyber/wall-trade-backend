"""Supabase JWT validation — HS256 (legacy) and JWKS (ES256/RS256)."""
from __future__ import annotations

import time
from threading import Lock
from typing import Any

import httpx
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwk, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import Settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

JWKS_TTL_SECONDS = 3600
_jwks_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_jwks_lock = Lock()


def _jwks_url(supabase_url: str) -> str:
    return f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


def _fetch_jwks(supabase_url: str) -> dict[str, Any]:
    """Fetch and cache Supabase JWKS (TTL 1 hour)."""
    now = time.time()
    with _jwks_lock:
        cached = _jwks_cache.get(supabase_url)
        if cached and now - cached[0] < JWKS_TTL_SECONDS:
            return cached[1]

    with httpx.Client(timeout=10.0) as client:
        response = client.get(_jwks_url(supabase_url))
        response.raise_for_status()
        jwks: dict[str, Any] = response.json()

    with _jwks_lock:
        _jwks_cache[supabase_url] = (now, jwks)
    return jwks


def clear_jwks_cache() -> None:
    """Clear JWKS cache (for tests)."""
    with _jwks_lock:
        _jwks_cache.clear()


def _decode_hs256(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.SUPABASE_JWT_SECRET:
        raise AuthenticationError(
            "SUPABASE_JWT_SECRET is not configured",
            error_code="TOKEN_INVALID",
        )
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )


def _decode_jwks(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.SUPABASE_URL:
        raise AuthenticationError(
            "SUPABASE_URL is not configured for JWKS validation",
            error_code="TOKEN_INVALID",
        )

    header = jwt.get_unverified_header(token)
    alg = header.get("alg")
    kid = header.get("kid")

    if not alg:
        raise JWTError("JWT header missing alg")

    jwks = _fetch_jwks(settings.SUPABASE_URL)
    keys = jwks.get("keys", [])

    for key_data in keys:
        if kid is not None and key_data.get("kid") != kid:
            continue
        signing_key = jwk.construct(key_data)
        return jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            options={"verify_aud": False},
        )

    raise JWTError(f"No matching JWK for kid={kid!r}")


def _decode_supabase_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode a Supabase access token using HS256 secret or JWKS."""
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "HS256")

    if alg == "HS256":
        return _decode_hs256(token, settings)
    if alg in ("ES256", "RS256"):
        return _decode_jwks(token, settings)

    raise JWTError(f"Unsupported JWT algorithm: {alg}")


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

    try:
        payload = _decode_supabase_token(credentials.credentials, settings)
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
