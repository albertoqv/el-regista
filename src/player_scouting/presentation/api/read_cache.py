"""Bulk reads kept in memory between requests.

Twins, the explorer and the forecasts read whole tables (every player's season, every
team match). On Neon's free plan each read counts against a 5 GB monthly network
allowance, so the same read is answered from memory for a few hours. Ingestion runs on
another machine, so a Vercel instance cannot hear about new data: the time limit is
what brings it in (data changes twice a week).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

TTL_SECONDS = 3 * 3600
# Distinct reads kept (each league and season set is one); the oldest leaves first.
MAX_ENTRIES = 256


class ReadCache:
    def __init__(
        self,
        ttl_seconds: float = TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        max_entries: int = MAX_ENTRIES,
    ) -> None:
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._entries: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_load(self, key: str, load: Callable[[], Any]) -> Any:
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and self._clock() - entry[0] <= self._ttl:
                return entry[1]
        value = load()
        with self._lock:
            self._entries.pop(key, None)
            self._entries[key] = (self._clock(), value)
            while len(self._entries) > self._max_entries:
                del self._entries[next(iter(self._entries))]
        return value

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


class _CachedReads:
    def __init__(self, inner: object, cache: ReadCache, methods: set[str]) -> None:
        self._inner = inner
        self._cache = cache
        self._methods = methods

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._inner, name)
        if name not in self._methods:
            return attribute

        def read(*args: Any, **kwargs: Any) -> Any:
            # Keyword arguments are time windows ("from now on"): new on every call.
            if kwargs:
                return attribute(*args, **kwargs)
            key = repr((type(self._inner).__name__, name, args))
            value = self._cache.get_or_load(key, lambda: attribute(*args))
            # A fresh container each time: callers may sort or extend what they get.
            if isinstance(value, list):
                return list(value)
            if isinstance(value, dict):
                return dict(value)
            return value

        return read


def cached_reads[T](inner: T, cache: ReadCache, methods: set[str]) -> T:
    """`inner` with the named read methods answered from `cache`."""
    return _CachedReads(inner, cache, methods)  # type: ignore[return-value]


# One per process: shared by every request this instance serves.
READ_CACHE = ReadCache()
