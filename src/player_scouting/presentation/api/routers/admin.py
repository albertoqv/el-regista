from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated, Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Query, Request, Response

from player_scouting.application.ports import (
    HostingUsage,
    HostingUsageProvider,
    VisitRepository,
)
from player_scouting.application.use_cases.admin_dashboard import (
    AdminDashboardUseCase,
    RecordVisitUseCase,
    is_bot,
)
from player_scouting.infrastructure.persistence.overview import DataFreshness
from player_scouting.presentation.api.dependencies import (
    get_data_freshness,
    get_database_overview,
    get_database_ping,
    get_hosting_usage_provider,
    get_visit_repository,
)
from player_scouting.presentation.api.security import (
    ADMIN_SESSION_SECONDS,
    admin_token,
    verify_admin,
    verify_ingestion_api_key,
)
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings

public_router = APIRouter(tags=["admin"])
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin)],
)

VisitRepositoryDep = Annotated[VisitRepository, Depends(get_visit_repository)]
SettingsDep = Annotated[ApiSettings, Depends(get_api_settings)]
HostingDep = Annotated[HostingUsageProvider | None, Depends(get_hosting_usage_provider)]
HOSTING_CACHE_SECONDS = 300
_hosting_cache: dict[str, tuple[float, HostingUsage]] = {}


@public_router.post("/admin/session", dependencies=[Depends(verify_ingestion_api_key)])
def open_admin_session(settings: SettingsDep) -> dict[str, str]:
    """Trades the key for a week-long session, so the browser never keeps the key."""
    expires_at = int(time.time()) + ADMIN_SESSION_SECONDS
    return {"token": admin_token(settings.ingestion_api_key, expires_at)}


@public_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@public_router.get("/health/db")
def database_health(
    ping: Annotated[Callable[[], None], Depends(get_database_ping)],
) -> dict[str, Any]:
    """Time of one round trip to the database (after a warm-up), in milliseconds."""
    ping()
    start = time.perf_counter()
    ping()
    return {
        "status": "ok",
        "round_trip_ms": round((time.perf_counter() - start) * 1000, 1),
    }


@public_router.get("/health/data")
def data_health(
    report: Annotated[DataFreshness, Depends(get_data_freshness)],
    response: Response,
) -> dict[str, Any]:
    """503 when played matches lack their result, so a monitor can alert on it."""
    stale = bool(report.missing_results)
    if stale:
        response.status_code = 503
    return {
        "status": "stale" if stale else "ok",
        "missing_results": report.missing_results,
        # Informative only: FBref and Understat refresh on different days.
        "goal_mismatches": report.goal_mismatches,
        "latest_result": report.latest_result.isoformat()
        if report.latest_result
        else None,
    }


def _client_ip(request: Request) -> str:
    # Railway's proxy puts the real client first in X-Forwarded-For.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@public_router.post("/metrics/visit", status_code=204)
async def record_visit(
    request: Request, visits: VisitRepositoryDep, settings: SettingsDep
) -> Response:
    # The web sends it as text/plain so the browser needs no CORS preflight.
    try:
        body = json.loads(await request.body())
        path = str(body["path"])
        referrer = body.get("referrer")
    except ValueError, KeyError, TypeError:
        return Response(status_code=204)
    # Semgrep takes this .execute() for a raw SQL cursor; it is a use case (ORM).
    RecordVisitUseCase(  # nosemgrep
        visits,
        salt=settings.visit_salt or settings.ingestion_api_key or "elregista",
        own_hosts=tuple(
            urlsplit(origin).hostname or "" for origin in settings.cors_origins_list
        ),
    ).execute(
        path,
        str(referrer) if referrer else None,
        _client_ip(request),
        request.headers.get("user-agent", ""),
    )
    return Response(status_code=204)


@public_router.post("/metrics/error", status_code=204)
async def record_client_error(request: Request) -> Response:
    """A JavaScript error from a visitor's browser (text/plain: no preflight)."""
    if is_bot(request.headers.get("user-agent", "")):
        return Response(status_code=204)
    try:
        body = json.loads(await request.body())
        message, path = str(body["message"]), str(body.get("path") or "/")
    except ValueError, KeyError, TypeError:
        return Response(status_code=204)
    request.app.state.client_errors.record(message, path)
    return Response(status_code=204)


class _CachedHosting:
    """Railway's numbers move slowly: ask at most every few minutes."""

    def __init__(self, provider: HostingUsageProvider) -> None:
        self._provider = provider

    def current_usage(self) -> HostingUsage:
        cached = _hosting_cache.get("usage")
        if cached and time.monotonic() - cached[0] < HOSTING_CACHE_SECONDS:
            return cached[1]
        usage = self._provider.current_usage()
        _hosting_cache["usage"] = (time.monotonic(), usage)
        return usage


@router.get("/dashboard")
def dashboard(
    request: Request,
    visits: VisitRepositoryDep,
    hosting: HostingDep,
    data: Annotated[dict[str, int], Depends(get_database_overview)],
    quality: Annotated[DataFreshness, Depends(get_data_freshness)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> dict[str, Any]:
    result = AdminDashboardUseCase(
        visits, _CachedHosting(hosting) if hosting else None
    ).execute(days)
    body = asdict(result)
    body["hosting_configured"] = hosting is not None
    body["data"] = data
    body["api"] = request.app.state.metrics.snapshot()
    body["client_errors"] = request.app.state.client_errors.snapshot()
    body["data_quality"] = {
        "missing_results": quality.missing_results,
        "goal_mismatches": quality.goal_mismatches,
        "latest_result": quality.latest_result.isoformat()
        if quality.latest_result
        else None,
    }
    return body
