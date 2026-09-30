from datetime import date, datetime

from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.presentation.api.dependencies import (
    get_match_stats_repository,
    get_player_repository,
    get_prediction_log,
    get_shot_repository,
    get_team_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.routers import ingestion as ingestion_router
from player_scouting.presentation.api.routers import players as players_router
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings
from tests.application.doubles import InMemoryPlayerRepository, InMemoryPredictionLog
from tests.application.test_hot_players import _repository as rosters
from tests.application.test_match_insights import _stats_repository
from tests.application.test_team_analytics import _repository as team_repository


def _client(log):
    app = create_app()
    teams = team_repository()
    stats = _stats_repository()
    shots = rosters()
    players = InMemoryPlayerRepository()
    players.save_player(
        Player(77, "Striker Name", "Forward", None, photo_url="https://x/p.jpg")
    )
    players.set_understat_id(77, 1)
    app.dependency_overrides[get_team_repository] = lambda: teams
    app.dependency_overrides[get_match_stats_repository] = lambda: stats
    app.dependency_overrides[get_shot_repository] = lambda: shots
    app.dependency_overrides[get_player_repository] = lambda: players
    app.dependency_overrides[get_prediction_log] = lambda: log
    app.dependency_overrides[get_api_settings] = lambda: ApiSettings(
        ingestion_api_key=""
    )
    return TestClient(app)


def test_snapshot_then_track_record(monkeypatch):
    monkeypatch.setattr(ingestion_router, "_now", lambda: datetime(2026, 10, 1))
    log = InMemoryPredictionLog()
    client = _client(log)

    saved = client.post("/ingestion/predictions/snapshot?days=90").json()
    body = client.get("/predictions/track-record?season=2026").json()

    assert saved["saved"] == 2  # both unplayed fixtures of the test calendar
    assert body["pending"] == 2
    assert body["live_total"]["matches"] == 0
    assert {"matches", "hits", "brier", "confident", "market_brier"} <= set(
        body["rebuilt_total"]
    )
    assert body["season_label"] == "2026"


def test_hot_players_link_to_our_players(monkeypatch):
    monkeypatch.setattr(players_router, "_today", lambda: date(2026, 9, 30))

    body = (
        _client(InMemoryPredictionLog())
        .get("/players/hot?season=2026&competition=La%20Liga")
        .json()
    )

    top = body["players"][0]
    assert (top["player_id"], top["name"], top["goals"]) == (77, "Striker Name", 4)
    assert top["photo_url"] == "https://x/p.jpg"
    assert body["window_start"] == "2026-08-31"
