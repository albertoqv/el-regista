from __future__ import annotations

import time
from collections import Counter, deque
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

SAMPLES = 2000
SLOW_MS = 2000

CallNext = Callable[[Request], Awaitable[Response]]


class RequestMetrics:
    """API health since the last deploy (kept in memory: free and good enough)."""

    def __init__(self) -> None:
        self.started_at = datetime.now(UTC)
        self.requests = 0
        self.server_errors = 0
        self.routes: Counter[str] = Counter()
        self.slow_routes: Counter[str] = Counter()
        self._durations: deque[float] = deque(maxlen=SAMPLES)

    def record(self, route: str, status: int, milliseconds: float) -> None:
        self.requests += 1
        if status >= 500:
            self.server_errors += 1
        self.routes[route] += 1
        if milliseconds > SLOW_MS:
            self.slow_routes[route] += 1
        self._durations.append(milliseconds)

    def _percentile(self, share: float) -> float:
        if not self._durations:
            return 0.0
        ordered = sorted(self._durations)
        return round(ordered[min(len(ordered) - 1, int(share * len(ordered)))], 1)

    def snapshot(self) -> dict[str, Any]:
        return {
            "since": self.started_at.isoformat(),
            "requests": self.requests,
            "server_errors": self.server_errors,
            "p50_ms": self._percentile(0.5),
            "p95_ms": self._percentile(0.95),
            "top_routes": self.routes.most_common(10),
            "slow_routes": self.slow_routes.most_common(5),
        }


def metrics_middleware(
    metrics: RequestMetrics,
) -> Callable[[Request, CallNext], Awaitable[Response]]:
    async def middleware(request: Request, call_next: CallNext) -> Response:
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            if request.method != "OPTIONS":
                route = getattr(request.scope.get("route"), "path", "(sin ruta)")
                metrics.record(
                    f"{request.method} {route}",
                    status,
                    (time.perf_counter() - start) * 1000,
                )

    return middleware
