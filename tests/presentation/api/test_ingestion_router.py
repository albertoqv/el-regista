from datetime import date

from fastapi.testclient import TestClient

from player_scouting.application.ports import (
    CompetitionStatisticsResult,
    MarketValueHistoryResult,
    PlayerCompetitionStats,
    PlayerSeasonResult,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.presentation.api.dependencies import (
    get_birth_date_provider,
    get_market_value_provider,
    get_player_repository,
    get_player_season_statistics_provider,
    get_statistics_provider,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    FakeBirthDateProvider,
    FakeCompetitionStatisticsProvider,
    FakeMarketValueProvider,
    FakePlayerSeasonStatisticsProvider,
    InMemoryPlayerRepository,
)

WORLD_CUP_2018 = Season("FIFA World Cup", "2018")
PREMIER_LEAGUE_2023 = Season("Premier League", "2023")


def test_ingest_statsbomb_competition_returns_a_summary_and_persists_players():
    stats_provider = FakeCompetitionStatisticsProvider(
        CompetitionStatisticsResult(
            WORLD_CUP_2018,
            [
                PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5),
                PlayerCompetitionStats(2, "Unknown Player", "Midfielder", None, 1, 1),
            ],
        )
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
    assert repository.get_player(1) is not None


def test_ingest_api_football_player_returns_a_summary_and_persists_the_player():
    provider = FakePlayerSeasonStatisticsProvider(
        PlayerSeasonResult(
            player_id=1,
            name="E. Haaland",
            position="Attacker",
            date_of_birth=date(2000, 7, 21),
            season=PREMIER_LEAGUE_2023,
            statistics=Statistics(36, 8),
        )
    )
    repository = InMemoryPlayerRepository()
    app = create_app()
    app.dependency_overrides[get_player_season_statistics_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post(
        "/ingestion/api-football/players?name=Haaland&league=39&season=2023"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 1
    assert repository.get_player(1).name == "E. Haaland"


def test_ingest_api_football_player_reports_when_the_player_is_not_found():
    provider = FakePlayerSeasonStatisticsProvider(None)
    repository = InMemoryPlayerRepository()
    app = create_app()
    app.dependency_overrides[get_player_season_statistics_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post(
        "/ingestion/api-football/players?name=Nobody&league=39&season=2023"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 0
    assert len(body["skipped"]) == 1


def test_ingest_transfermarkt_player_persists_foot_and_market_value_history():
    provider = FakeMarketValueProvider(
        MarketValueHistoryResult(
            preferred_foot="right",
            points=[MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid")],
        )
    )
    repository = InMemoryPlayerRepository()
    repository.save_player(
        Player(1, "Jude Bellingham", "Midfielder", date(2003, 6, 29))
    )
    app = create_app()
    app.dependency_overrides[get_market_value_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post(
        "/ingestion/transfermarkt/players?player_id=1&name=Jude Bellingham"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 1
    assert repository.get_player(1).preferred_foot == "right"
    assert len(repository.list_market_value_history(1)) == 1


def test_ingest_transfermarkt_player_reports_when_the_player_is_not_found():
    provider = FakeMarketValueProvider(None)
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Nobody", "Midfielder", date(2003, 6, 29)))
    app = create_app()
    app.dependency_overrides[get_market_value_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post("/ingestion/transfermarkt/players?player_id=1&name=Nobody")

    assert response.status_code == 200
    body = response.json()
    assert body["ingested"] == 0
    assert len(body["skipped"]) == 1
