from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from player_scouting.presentation.api.metrics import (
    RequestMetrics,
    metrics_middleware,
)
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
from player_scouting.presentation.api.settings import get_api_settings


def create_app() -> FastAPI:
    app = FastAPI(title="El Regista API")
    app.state.metrics = RequestMetrics()
    app.state.response_cache = ResponseCache()
    app.middleware("http")(response_cache_middleware(app.state.response_cache))
    app.middleware("http")(metrics_middleware(app.state.metrics))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_api_settings().cors_origins_list,
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
    return app


app = create_app()
