from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from player_scouting.application.ports import DataSourceUnavailableError
from player_scouting.presentation.api.client_errors import ClientErrorLog
from player_scouting.presentation.api.metrics import (
    RequestMetrics,
    metrics_middleware,
)
from player_scouting.presentation.api.rate_limit import (
    RateLimiter,
    rate_limit_middleware,
)
from player_scouting.presentation.api.read_cache import READ_CACHE
from player_scouting.presentation.api.response_cache import (
    ResponseCache,
    response_cache_middleware,
)
from player_scouting.presentation.api.routers import (
    admin,
    ingestion,
    insights,
    players,
    seasons,
    teams,
)
from player_scouting.presentation.api.security import (
    FailedAttempts,
    security_headers_middleware,
)
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    settings = settings or get_api_settings()
    docs = settings.expose_docs
    app = FastAPI(
        title="El Regista API",
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.failed_attempts = FailedAttempts()
    app.state.client_errors = ClientErrorLog()
    app.state.metrics = RequestMetrics()
    app.state.database_usage = {}
    app.state.response_cache = ResponseCache()
    app.middleware("http")(
        response_cache_middleware(app.state.response_cache, READ_CACHE.clear)
    )
    app.middleware("http")(metrics_middleware(app.state.metrics))
    # Outermost: a flood is refused before it costs any work.
    app.middleware("http")(
        rate_limit_middleware(RateLimiter(settings.rate_limit_per_minute))
    )
    # Around everything, so refusals (429, 401) carry the headers too.
    app.middleware("http")(security_headers_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(players.router)
    app.include_router(seasons.router)
    app.include_router(seasons.overview_router)
    app.include_router(teams.teams_router)
    app.include_router(insights.router)
    app.include_router(teams.predictions_router)
    app.include_router(ingestion.router)
    app.include_router(admin.public_router)
    app.include_router(admin.router)
    app.add_exception_handler(DataSourceUnavailableError, _source_down)
    return app


async def _source_down(request: Request, error: Exception) -> JSONResponse:
    # The refresh tells "the source is down, next run" apart from a bug of ours.
    return JSONResponse(status_code=503, content={"detail": str(error)})


app = create_app()
