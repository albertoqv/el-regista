from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.presentation.api.dependencies import (
    get_player_repository,
    get_shot_repository,
    get_team_repository,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import InMemoryPlayerRepository
from tests.application.test_player_markets import _rosters
from tests.application.test_team_analytics import _repository as team_repository


def _client():
    app = create_app()
    teams, shots = team_repository(), _rosters()
    players = InMemoryPlayerRepository()
    players.save_player(
        Player(77, "Striker", "Forward", None, photo_url="https://x/p.jpg")
    )
    players.set_understat_id(77, 1)
    app.dependency_overrides[get_team_repository] = lambda: teams
    app.dependency_overrides[get_shot_repository] = lambda: shots
    app.dependency_overrides[get_player_repository] = lambda: players
    return TestClient(app)


def test_player_markets_link_our_players():
    body = _client().get("/predictions/6/players").json()

    striker = next(line for line in body["home"] if line["name"] == "Striker")
    assert striker["player_id"] == 77
    assert striker["photo_url"] == "https://x/p.jpg"
    assert 0 < striker["goal"] < 1
    assert {"assist", "card", "shots_1", "shots_2", "expected_minutes"} <= set(striker)


def test_player_markets_backtest():
    body = (
        _client()
        .get(
            "/predictions/players-backtest",
            params={"competition": "La Liga", "season": "2026", "minimum_matches": 1},
        )
        .json()
    )

    assert body["predictions"] > 0
