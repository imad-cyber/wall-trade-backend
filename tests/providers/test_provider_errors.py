from app.core.exceptions import ExternalServiceError
from app.providers.capital_stake.provider_errors import (
    empty_stock_quote,
    is_recoverable_provider_error,
)


def test_recoverable_dns_failure():
    exc = ExternalServiceError("Capital Stake", "[Errno 11001] getaddrinfo failed")
    assert is_recoverable_provider_error(exc) is True


def test_recoverable_forbidden():
    exc = ExternalServiceError("Capital Stake", "Client error '403 Forbidden' for url")
    assert is_recoverable_provider_error(exc) is True


def test_non_recoverable_not_found():
    from app.core.exceptions import ResourceNotFoundError

    exc = ExternalServiceError("Capital Stake", "Ticker OGDC not found")
    assert is_recoverable_provider_error(exc) is False


def test_empty_stock_quote_shape():
    quote = empty_stock_quote("ogdc")
    assert quote.ticker == "OGDC"
    assert quote.price == 0.0
