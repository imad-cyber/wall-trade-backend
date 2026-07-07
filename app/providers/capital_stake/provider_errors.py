"""Capital Stake provider error classification and safe fallbacks."""
from app.api.v1.schemas.company import PriceRangeSchema, StockDataSchema, StockRangesSchema
from app.core.exceptions import ExternalServiceError
from app.providers.capital_stake.mapper import _iso_timestamp

_NETWORK_MARKERS = (
    "getaddrinfo failed",
    "name or service not known",
    "nodename nor servname",
    "connection refused",
    "connect timeout",
    "timed out",
    "network is unreachable",
    "no route to host",
    "temporary failure in name resolution",
)

# Error codes that mean "data is unavailable" rather than a hard failure.
# Callers that can degrade gracefully (e.g. show partial data) should check
# this before deciding whether to re-raise or substitute empty data.
_RECOVERABLE_CODES = frozenset({
    "SUBSCRIPTION_ERROR",  # endpoint not included in current plan
    "SERVICE_UNAVAILABLE",  # token not configured / provider unreachable
})


def is_recoverable_provider_error(exc: ExternalServiceError) -> bool:
    """True when the error is expected / unavoidable — callers may return empty data instead of 5xx.

    Covers:
    - Subscription errors  (endpoint not enabled for this account)
    - Service unavailable  (token not configured, network unreachable)

    Does NOT cover hard failures (5xx, auth mis-configuration) so those
    still surface as errors to aid debugging.
    """
    if exc.error_code in _RECOVERABLE_CODES:
        return True
    message = str(exc.message or exc).lower()
    return any(marker in message for marker in _NETWORK_MARKERS)


def empty_stock_quote(ticker: str) -> StockDataSchema:
    """Minimal quote payload when live CSAPI data is unavailable."""
    return StockDataSchema(
        ticker=ticker.upper(),
        name=ticker.upper(),
        price=0.0,
        change=0.0,
        change_percent=0.0,
        status="Closed",
        last_updated=_iso_timestamp(None),
        ranges=StockRangesSchema(
            day_range=PriceRangeSchema(low=0.0, high=0.0, current=0.0),
            week_52=PriceRangeSchema(low=0.0, high=0.0, current=0.0),
        ),
    )
