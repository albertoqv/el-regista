from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from starlette.responses import Response

from player_scouting.presentation.api.settings import ApiSettings, get_api_settings

# Wrong keys allowed from one address in the window before it is blocked.
MAX_FAILED_ATTEMPTS = 10
FAILED_WINDOW_SECONDS = 15 * 60
ADMIN_SESSION_SECONDS = 7 * 24 * 3600


def client_address(request: Request) -> str:
    """The address Railway's proxy saw: the last hop, which a client cannot forge."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else ""


class FailedAttempts:
    """Wrong keys per address, in memory: enough to stop guessing for free."""

    def __init__(self) -> None:
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def _recent(self, address: str) -> deque[float]:
        attempts = self._attempts[address]
        while attempts and time.monotonic() - attempts[0] > FAILED_WINDOW_SECONDS:
            attempts.popleft()
        return attempts

    def blocked(self, address: str) -> bool:
        return len(self._recent(address)) >= MAX_FAILED_ATTEMPTS

    def record(self, address: str) -> None:
        self._recent(address).append(time.monotonic())


def _attempts(request: Request) -> FailedAttempts:
    attempts = getattr(request.app.state, "failed_attempts", None)
    if attempts is None:
        attempts = request.app.state.failed_attempts = FailedAttempts()
    return attempts


def admin_token(key: str, expires_at: int) -> str:
    """An expiring session signed with the key; the key itself never leaves."""
    signature = hmac.new(
        key.encode(), f"admin|{expires_at}".encode(), hashlib.sha256
    ).hexdigest()
    return f"{expires_at}.{signature}"


def _valid_admin_token(key: str, token: str) -> bool:
    expires, _, _ = token.partition(".")
    if not expires.isdigit() or int(expires) < time.time():
        return False
    return hmac.compare_digest(token, admin_token(key, int(expires)))


def _check(
    request: Request, settings: ApiSettings, key: str | None, token: str | None
) -> None:
    if not settings.ingestion_api_key:
        if settings.require_ingestion_key:
            raise HTTPException(status_code=503, detail="Ingestion is not configured")
        return
    address = client_address(request)
    attempts = _attempts(request)
    if attempts.blocked(address):
        raise HTTPException(status_code=429, detail="Too many wrong keys")
    if key is not None and hmac.compare_digest(
        key.encode(), settings.ingestion_api_key.encode()
    ):
        return
    if token is not None and _valid_admin_token(settings.ingestion_api_key, token):
        return
    attempts.record(address)
    raise HTTPException(status_code=401, detail="Invalid or missing ingestion API key")


def verify_ingestion_api_key(
    request: Request,
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
    x_ingestion_key: Annotated[str | None, Header()] = None,
) -> None:
    _check(request, settings, x_ingestion_key, None)


def verify_admin(
    request: Request,
    settings: Annotated[ApiSettings, Depends(get_api_settings)],
    x_ingestion_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """The admin panel: the key, or a session token obtained with it."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    _check(request, settings, x_ingestion_key, token)


# Sent with every answer (OWASP ZAP baseline, Oct 2026): no MIME sniffing of the JSON,
# and no other site may embed the API's responses (the web reads them through its own
# /api proxy, so same-origin is enough).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Cross-Origin-Resource-Policy": "same-origin",
}


async def security_headers_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    # The web posts visits and browser errors straight here from its own site.
    if request.url.path.startswith("/metrics/"):
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response
