"""Prometheus metrics for WallTrade backend."""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

request_total = Counter(
    "walltrade_request_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"],
)
request_latency_ms = Histogram(
    "walltrade_request_latency_ms",
    "HTTP request latency in milliseconds",
    ["endpoint"],
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)
cache_hit_total = Counter(
    "walltrade_cache_hit_total",
    "Cache hits by type",
    ["type"],
)
ai_latency_ms = Histogram(
    "walltrade_ai_latency_ms",
    "AI provider latency in milliseconds",
    ["model"],
    buckets=(100, 250, 500, 1000, 2500, 5000, 10000, 30000),
)
external_api_latency_ms = Histogram(
    "walltrade_external_api_latency_ms",
    "External API latency in milliseconds",
    ["provider"],
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)


def record_request_total(endpoint: str, method: str, status: int) -> None:
    request_total.labels(endpoint=endpoint, method=method, status=str(status)).inc()


def record_request_latency(endpoint: str, latency_ms: float) -> None:
    request_latency_ms.labels(endpoint=endpoint).observe(latency_ms)


def record_cache_hit(cache_type: str) -> None:
    cache_hit_total.labels(type=cache_type).inc()


def record_ai_latency(model: str, latency_ms: float) -> None:
    ai_latency_ms.labels(model=model).observe(latency_ms)


def record_external_api_latency(provider: str, latency_ms: float) -> None:
    external_api_latency_ms.labels(provider=provider).observe(latency_ms)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
