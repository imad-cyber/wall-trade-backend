"""OpenTelemetry tracing helpers (stub — expand in production)."""
from contextlib import contextmanager
from typing import Iterator, Optional


@contextmanager
def start_span(name: str, attributes: Optional[dict] = None) -> Iterator[None]:
    """No-op span stub until full OTEL wiring is configured."""
    yield
