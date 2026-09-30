from fastapi.testclient import TestClient

from player_scouting.presentation.api.dependencies import (
    get_match_stats_provider,
    get_match_stats_repository,
    get_shot_repository,
    get_team_repository,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    InMemoryMatchStatsRepository,
    InMemoryShotRepository,
)
from tests.application.test_match_insights import _stats, _stats_repository
from tests.application.test_team_analytics import _repository as team_repository


def _client(stats=None, provider=None) -> TestClient:
    app = create_app()
    teams = team_repository()
    stats = stats or _stats_repository()
    app.dependency_overrides[get_team_repository] = lambda: teams
    app.dependency_overrides[get_match_stats_repository] = lambda: stats
    app.dependency_overrides[get_shot_repository] = InMemoryShotRepository
    if provider is not None:
        app.dependency_overrides[get_match_stats_provider] = lambda: provider
    return TestClient(app)


def test_match_insights():
    body = _client().get("/predictions/6/insights").json()

    assert body["home_team"] == "Barcelona"
    assert set(body["result"]) >= {"home_win", "draw", "away_win"}
    assert body["market"]["home_win"] > 0.7
    assert [line["line"] for line in body["goals_over"]] == [0.5, 1.5, 2.5, 3.5, 4.5]
    corners = next(s for s in body["stats"] if s["stat"] == "corners")
    assert corners["expected_home"] > corners["expected_away"]
    assert len(corners["over"]) == 5
    assert body["referee"]["name"] == "Ref Strict"
    assert len(body["head_to_head"]) == 2


def test_insights_for_an_unknown_match_is_404():
    assert _client().get("/predictions/999/insights").status_code == 404


def test_stats_backtest():
    body = (
        _client()
        .get(
            "/predictions/stats-backtest",
            params={"competition": "La Liga", "season": "2026", "minimum_history": 2},
        )
        .json()
    )

    assert body[0]["stat"] in {
        "corners",
        "yellows",
        "fouls",
        "shots",
        "shots_on_target",
    }
    assert "model_mae" in body[0]


def test_ingest_football_data():
    class Provider:
        def season(self, start_year):
            return [_stats(1, "Barcelona", "Getafe", 3, 0)]

        def upcoming(self):
            return []

    stats = InMemoryMatchStatsRepository()
    response = _client(stats, Provider()).post("/ingestion/football-data/seasons/2026")

    assert response.json() == {"saved": 1}
