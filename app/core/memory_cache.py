"""In-memory TTL cache for hot read paths (quotes, overview)."""
import time
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: float
    created_at: float

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at

    @property
    def age_seconds(self) -> int:
        return max(0, int(time.monotonic() - self.created_at))


class MemoryCache:
    """Thread-unsafe in-process cache — sufficient for single-worker dev/UAT."""

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry[Any]] = {}

    def get(self, key: str) -> Optional[tuple[Any, int]]:
        entry = self._store.get(key)
        if entry is None or entry.is_expired:
            if entry is not None:
                del self._store[key]
            return None
        return entry.value, entry.age_seconds

    def set(self, key: str, value: T, ttl_seconds: float) -> None:
        now = time.monotonic()
        self._store[key] = CacheEntry(
            value=value,
            expires_at=now + ttl_seconds,
            created_at=now,
        )

    def get_stale(self, key: str) -> Optional[tuple[Any, int]]:
        """Return last stored value even if TTL expired (provider-error fallback)."""
        entry = self._store.get(key)
        if entry is None:
            return None
        return entry.value, entry.age_seconds

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


_memory_cache = MemoryCache()


def get_memory_cache() -> MemoryCache:
    return _memory_cache
