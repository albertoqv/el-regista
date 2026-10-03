from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from player_scouting.presentation.api.security import client_address

WINDOW_SECONDS = 60
CallNext = Callable[[Request], Awaitable[Response]]


class RateLimiter:
    """Sliding one-minute window per address, in memory."""

    def __init__(self, limit: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, address: str) -> bool:
        now = self._clock()
        hits = self._hits[address]
        while hits and now - hits[0] > WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        if len(self._hits) > 10_000:
            # Forget idle addresses so memory stays bounded.
            for key in [k for k, v in self._hits.items() if not v]:
                del self._hits[key]
        return True


def rate_limit_middleware(
    limiter: RateLimiter,
) -> Callable[[Request, CallNext], Awaitable[Response]]:
    async def middleware(request: Request, call_next: CallNext) -> Response:
        if request.method != "OPTIONS" and not limiter.allow(client_address(request)):
            return JSONResponse(
                {"detail": "Too many requests"},
                status_code=429,
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )
        return await call_next(request)

    return middleware
