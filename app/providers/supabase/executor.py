"""Supabase query execution with APIError mapping."""
from typing import Any

from postgrest.exceptions import APIError

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_response_data(response: Any) -> Any:
    return getattr(response, "data", response)


def execute_query(query, *, table: str = "", operation: str = ""):
    """Execute a Supabase query builder and map APIError to AppException."""
    try:
        result = query.execute()
        if table:
            logger.debug("Supabase %s on %s succeeded", operation or "query", table)
        return result
    except APIError as exc:
        code = getattr(exc, "code", None)
        payload = getattr(exc, "args", [{}])[0] if getattr(exc, "args", None) else {}
        if isinstance(payload, dict):
            code = payload.get("code", code)
            message = payload.get("message", str(exc))
        else:
            message = str(exc)
        if code == "42501":
            raise AppException(
                "Supabase table access is denied. Send a valid Supabase user JWT "
                "in the Authorization header or adjust RLS policies for this role.",
                status_code=503,
                error_code="SUPABASE_CONFIGURATION_ERROR",
            )
        logger.error("Supabase query failed on %s: %s", table or "unknown", message)
        raise AppException(
            f"Supabase query failed: {message}",
            status_code=502,
            error_code="SUPABASE_QUERY_ERROR",
        ) from exc
