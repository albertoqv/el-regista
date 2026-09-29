from datetime import date

from fastapi.testclient import TestClient

from player_scouting.application.ports import PlayerCompetitionStats
from player_scouting.presentation.api.dependencies import (
    get_birth_date_provider,
    get_player_repository,
    get_statistics_provider,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    FakeBirthDateProvider,
    FakeCompetitionStatisticsProvider,
    InMemoryPlayerRepository,
)


def test_ingest_statsbomb_competition_returns_a_summary_and_persists_players():
    stats_provider = FakeCompetitionStatisticsProvider(
        [
            PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5),
            PlayerCompetitionStats(2, "Unknown Player", "Midfielder", None, 1, 1),
        ]
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    app = create_app()
    app.dependency_overrides[get_statistics_provider] = lambda: stats_provider
    app.dependency_overrides[get_birth_date_provider] = lambda: birth_date_provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post("/ingestion/statsbomb/43/3")

    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 1
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["player_id"] == 2
    assert repository.get(1) is not None
