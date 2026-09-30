from __future__ import annotations

import json
import time
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
)
from player_scouting.presentation.api.dependencies import (
    get_database_overview,
    get_hosting_usage_provider,
    get_visit_repository,
)
from player_scouting.presentation.api.security import verify_ingestion_api_key
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings

public_router = APIRouter(tags=["admin"])
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_ingestion_api_key)],
)

VisitRepositoryDep = Annotated[VisitRepository, Depends(get_visit_repository)]
SettingsDep = Annotated[ApiSettings, Depends(get_api_settings)]
HostingDep = Annotated[HostingUsageProvider | None, Depends(get_hosting_usage_provider)]
HOSTING_CACHE_SECONDS = 300
_hosting_cache: dict[str, tuple[float, HostingUsage]] = {}


@public_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
    RecordVisitUseCase(
        visits,
        salt=settings.visit_salt or settings.ingestion_api_key or "talentscope",
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
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> dict[str, Any]:
    result = AdminDashboardUseCase(
        visits, _CachedHosting(hosting) if hosting else None
    ).execute(days)
    body = asdict(result)
    body["hosting_configured"] = hosting is not None
    body["data"] = data
    body["api"] = request.app.state.metrics.snapshot()
    return body
