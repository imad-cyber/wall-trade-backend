"""Shared request validators."""
import re

from fastapi import Path

TICKER_PATTERN = re.compile(r"^[A-Z0-9./-]{1,10}$", re.IGNORECASE)


def validate_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not TICKER_PATTERN.match(normalized):
        from app.core.exceptions import AppException

        raise AppException(
            f"Invalid ticker format: {ticker}",
            status_code=400,
            error_code="TICKER_INVALID",
        )
    return normalized


def TickerPath(
    description: str = "PSX ticker symbol",
) -> str:
    return Path(..., description=description, min_length=1, max_length=10)
