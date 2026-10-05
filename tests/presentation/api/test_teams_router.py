from fastapi.testclient import TestClient

from player_scouting.presentation.api.dependencies import (
    get_shot_repository,
    get_team_data_provider,
    get_team_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.routers import teams
from tests.application.doubles import InMemoryShotRepository
from tests.application.test_team_analytics import NOW, FakeTeamProvider, _repository


def _client(repository=None, provider=None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_team_repository] = lambda: repository or _repository()
    app.dependency_overrides[get_shot_repository] = InMemoryShotRepository
    if provider is not None:
        app.dependency_overrides[get_team_data_provider] = lambda: provider
    return TestClient(app)


def test_league_table():
    body = _client().get("/teams/table?season=2026&competition=La Liga").json()

    assert body[0]["team"] == "Barcelona"
    assert body[0]["points"] == 10
    assert body[0]["form"] == ["w", "d", "w", "w"]


def test_team_matches():
    body = _client().get("/teams/matches?team=Barcelona&season=2026").json()

    assert [m["match_id"] for m in body] == [1, 3, 4, 5]
    assert body[0]["opponent"] == "Getafe"


def test_predictions_for_the_coming_days(monkeypatch):
    # Fixed clock: the fixture match (4 Oct 2026) must still be ahead.
    monkeypatch.setattr(teams, "_now", lambda: NOW)
    app_client = _client()

    body = app_client.get("/predictions?days=4000").json()

    assert body[0]["home_team"] == "Barcelona"
    assert (
        abs(body[0]["home_win"] + body[0]["draw"] + body[0]["away_win"] - 1) < 1e-3
    )  # rounded to 4 decimals
    assert len(body[0]["scorelines"]) == 5
    assert "kickoff" in body[0]


def test_backtest():
    body = _client().get("/predictions/backtest?season=2026&minimum_history=1").json()

    assert body["matches"] == 4
    assert "calibration" in body


def test_ingest_team_season():
    repository = _repository()
    response = _client(repository, FakeTeamProvider()).post(
        "/ingestion/understat/teams/2026"
    )

    assert response.json() == {"fixtures": 1, "team_matches": 2}
