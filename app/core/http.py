"""Centralized async HTTP client with retries and observability."""
import time
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.observability.context import get_ctx
from app.observability.metrics import record_external_api_latency

logger = get_logger(__name__)

_registry: dict[str, "AsyncHTTPClient"] = {}


class AsyncHTTPClient:
    """Shared httpx.AsyncClient with retries, timeouts, and request ID propagation."""

    def __init__(
        self,
        base_url: str,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        api_key: Optional[str] = None,
        provider_name: str = "http",
    ):
        settings = get_settings()
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name
        self.api_key = api_key
        self.retries = retries if retries is not None else settings.DEFAULT_MAX_RETRIES
        timeout_val = timeout if timeout is not None else settings.DEFAULT_TIMEOUT_SECONDS
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_val),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        ctx = get_ctx()
        if ctx.request_id:
            headers["X-Request-ID"] = ctx.request_id
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        start = time.perf_counter()

        @retry(
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            reraise=True,
        )
        async def _do_request() -> httpx.Response:
            response = await self._client.request(method, url, headers=self._headers(), **kwargs)
            response.raise_for_status()
            return response

        try:
            response = await _do_request()
        except httpx.HTTPError as exc:
            logger.error("%s %s failed: %s", method, url, exc)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        record_external_api_latency(self.provider_name, elapsed_ms)
        ctx = get_ctx()
        ctx.provider_latencies[self.provider_name] = elapsed_ms
        logger.info(
            "HTTP %s %s -> %s (%.1fms)",
            method,
            url,
            response.status_code,
            elapsed_ms,
        )
        return response.json()

    async def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, body: Optional[dict] = None) -> dict[str, Any]:
        return await self._request("POST", path, json=body or {})

    async def aclose(self) -> None:
        await self._client.aclose()


def get_http_client(
    name: str,
    base_url: str,
    api_key: Optional[str] = None,
) -> AsyncHTTPClient:
    """Get or create a named HTTP client from the registry."""
    registry_key = f"{name}:{base_url.rstrip('/')}"
    existing = _registry.get(registry_key)
    if existing is not None:
        if api_key and existing.api_key != api_key:
            existing.api_key = api_key
        return existing
    _registry[registry_key] = AsyncHTTPClient(
        base_url,
        api_key=api_key,
        provider_name=name,
    )
    return _registry[registry_key]


def get_http_client_registry() -> dict[str, AsyncHTTPClient]:
    return _registry


async def close_http_clients() -> None:
    for client in _registry.values():
        await client.aclose()
    _registry.clear()
