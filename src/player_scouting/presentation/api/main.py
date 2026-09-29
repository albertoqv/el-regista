from __future__ import annotations

from fastapi import FastAPI

from player_scouting.presentation.api.routers import ingestion, players


def create_app() -> FastAPI:
    app = FastAPI(title="Player Scouting API")
    app.include_router(players.router)
    app.include_router(ingestion.router)
    return app


app = create_app()
