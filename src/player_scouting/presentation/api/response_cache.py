from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

# Data only changes when something is ingested (and that empties the cache), so
# the time limit is for answers that depend on the clock: "next 7 days", "today".
TTL_SECONDS = 600
# Railway bills memory: a hard cap, the least used answers leave first.
MAX_BYTES = 32 * 1024 * 1024
CACHEABLE_PREFIXES = ("/players", "/seasons", "/teams", "/predictions", "/overview")

CallNext = Callable[[Request], Awaitable[Response]]


class ResponseCache:
    """Finished GET answers by URL, least recently used first out."""

    def __init__(
        self,
        ttl_seconds: float = TTL_SECONDS,
        max_bytes: int = MAX_BYTES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._max_bytes = max_bytes
        self._clock = clock
        self._entries: OrderedDict[str, tuple[float, bytes, str]] = OrderedDict()
        self._bytes = 0

    def get(self, key: str) -> tuple[bytes, str] | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, body, media_type = entry
        if self._clock() - stored_at > self._ttl:
            self._remove(key)
            return None
        self._entries.move_to_end(key)
        return body, media_type

    def put(self, key: str, body: bytes, media_type: str) -> None:
        if len(body) > self._max_bytes:
            return
        if key in self._entries:
            self._remove(key)
        self._entries[key] = (self._clock(), body, media_type)
        self._bytes += len(body)
        while self._bytes > self._max_bytes:
            self._remove(next(iter(self._entries)))

    def clear(self) -> None:
        self._entries.clear()
        self._bytes = 0

    def _remove(self, key: str) -> None:
        _, body, _ = self._entries.pop(key)
        self._bytes -= len(body)


def response_cache_middleware(
    cache: ResponseCache, *also_clear: Callable[[], None]
) -> Callable[[Request, CallNext], Awaitable[Response]]:
    async def middleware(request: Request, call_next: CallNext) -> Response:
        path = request.url.path
        if request.method == "POST" and path.startswith("/ingestion"):
            try:
                return await call_next(request)
            finally:
                cache.clear()
                for clear in also_clear:
                    clear()
        if request.method != "GET" or not path.startswith(CACHEABLE_PREFIXES):
            return await call_next(request)

        key = f"{path}?{request.url.query}"
        cached = cache.get(key)
        if cached is not None:
            body, media_type = cached
            return Response(body, media_type=media_type, headers={"X-Cache": "HIT"})

        response = await call_next(request)
        if response.status_code != 200:
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])  # type: ignore[attr-defined]
        media_type = response.headers.get("content-type", "application/json")
        cache.put(key, body, media_type)
        headers = {
            name: value
            for name, value in response.headers.items()
            if name.lower() != "content-length"
        }
        headers["X-Cache"] = "MISS"
        return Response(body, status_code=200, headers=headers)

    return middleware
