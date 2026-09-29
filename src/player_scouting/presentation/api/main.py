from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from player_scouting.presentation.api.routers import ingestion, players
from player_scouting.presentation.api.settings import get_api_settings


def create_app() -> FastAPI:
    app = FastAPI(title="TalentScope API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_api_settings().cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(players.router)
    app.include_router(ingestion.router)
    return app


app = create_app()
