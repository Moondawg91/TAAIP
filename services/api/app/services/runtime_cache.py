from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Hashable, Optional, Tuple


class TTLRUCache:
    """Small in-process TTL + LRU cache for read-heavy intelligence paths."""

    def __init__(self, maxsize: int = 256, ttl_seconds: int = 60) -> None:
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._store: "OrderedDict[Hashable, Tuple[float, Any]]" = OrderedDict()
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.time()

    def get(self, key: Hashable) -> Any:
        with self._lock:
            record = self._store.get(key)
            if record is None:
                return None
            expires_at, value = record
            if expires_at < self._now():
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: Hashable, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.ttl_seconds
        with self._lock:
            self._store[key] = (self._now() + ttl, value)
            self._store.move_to_end(key)
            while len(self._store) > self.maxsize:
                self._store.popitem(last=False)

    def delete(self, key: Hashable) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def cached_call(
    cache: TTLRUCache,
    key: Hashable,
    fn: Callable[[], Any],
    ttl_seconds: Optional[int] = None,
) -> Any:
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = fn()
    cache.set(key, value, ttl_seconds=ttl_seconds)
    return value


INTEL_CACHE_BUCKETS: Dict[str, TTLRUCache] = {
    "unit_scope": TTLRUCache(maxsize=512, ttl_seconds=300),
    "analytics_snapshot": TTLRUCache(maxsize=512, ttl_seconds=60),
    "recommendation_snapshot": TTLRUCache(maxsize=512, ttl_seconds=60),
    "frago_snapshot": TTLRUCache(maxsize=512, ttl_seconds=60),
    "version_list": TTLRUCache(maxsize=1024, ttl_seconds=45),
    "archive_event": TTLRUCache(maxsize=1024, ttl_seconds=45),
    "explanation": TTLRUCache(maxsize=1024, ttl_seconds=120),
}


def bucket(name: str) -> TTLRUCache:
    return INTEL_CACHE_BUCKETS[name]
