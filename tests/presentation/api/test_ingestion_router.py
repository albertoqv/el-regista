from datetime import date

from fastapi.testclient import TestClient

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.application.ports import (
    AdvancedSeasonRow,
    CompetitionStatisticsResult,
    LeaguePlayersPage,
    LeagueSummary,
    MarketValueHistoryResult,
    PlayerCompetitionStats,
    PlayerSeasonResult,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics
from player_scouting.presentation.api.dependencies import (
    get_advanced_season_provider,
    get_birth_date_provider,
    get_enrichment_pause,
    get_league_ingestion_job_repository,
    get_league_players_provider,
    get_league_search_provider,
    get_market_value_provider,
    get_player_repository,
    get_player_season_statistics_provider,
    get_season_dataset_provider,
    get_statistics_provider,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    FakeAdvancedSeasonProvider,
    FakeBirthDateProvider,
    FakeCompetitionStatisticsProvider,
    FakeLeaguePlayersProvider,
    FakeLeagueSearchProvider,
    FakeMarketValueProvider,
    FakePlayerSeasonStatisticsProvider,
    FakeSeasonDatasetProvider,
    InMemoryLeagueIngestionJobRepository,
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


def test_search_leagues_returns_real_shaped_results():
    provider = FakeLeagueSearchProvider(
        [LeagueSummary(id=135, name="Serie A", country="Italy")]
    )
    app = create_app()
    app.dependency_overrides[get_league_search_provider] = lambda: provider
    client = TestClient(app)

    response = client.get("/ingestion/leagues/search?q=Serie A")

    assert response.status_code == 200
    assert response.json() == [{"id": 135, "name": "Serie A", "country": "Italy"}]


def test_enqueue_league_ingestion_creates_a_job():
    job_repository = InMemoryLeagueIngestionJobRepository()
    app = create_app()
    app.dependency_overrides[get_league_ingestion_job_repository] = lambda: (
        job_repository
    )
    client = TestClient(app)

    response = client.post(
        "/ingestion/leagues?league_id=140&league_name=La Liga&season_year=2023"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["league_id"] == 140
    assert body["is_completed"] is False
    assert len(job_repository.list_jobs()) == 1


def test_list_league_ingestion_jobs_returns_their_progress():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    app = create_app()
    app.dependency_overrides[get_league_ingestion_job_repository] = lambda: (
        job_repository
    )
    client = TestClient(app)

    response = client.get("/ingestion/leagues")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["league_name"] == "La Liga"


def test_process_league_ingestion_batch_ingests_players_and_advances_jobs():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    players_provider = FakeLeaguePlayersProvider(
        {
            (140, 2023): [
                LeaguePlayersPage(
                    players=[
                        PlayerSeasonResult(
                            player_id=1,
                            name="Player One",
                            position="Forward",
                            date_of_birth=date(1995, 1, 1),
                            season=PREMIER_LEAGUE_2023,
                            statistics=Statistics(1, 1),
                        )
                    ],
                    current_page=1,
                    total_pages=1,
                )
            ]
        }
    )
    player_repository = InMemoryPlayerRepository()
    app = create_app()
    app.dependency_overrides[get_league_ingestion_job_repository] = lambda: (
        job_repository
    )
    app.dependency_overrides[get_league_players_provider] = lambda: players_provider
    app.dependency_overrides[get_player_repository] = lambda: player_repository
    client = TestClient(app)

    response = client.post("/ingestion/leagues/process?budget=5")

    assert response.status_code == 200
    body = response.json()
    assert body["pages_processed"] == 1
    assert body["players_ingested"] == 1
    assert player_repository.get_player(1) is not None


def test_ingest_fbref_season_persists_every_player_of_the_season():
    provider = FakeSeasonDatasetProvider(
        {
            2026: [
                PlayerSeasonResult(
                    player_id=1_500_000_000,
                    name="Jude Bellingham",
                    position="Midfielder",
                    date_of_birth=None,
                    birth_year=2003,
                    season=Season("La Liga", "2026"),
                    statistics=Statistics(3, 2),
                )
            ]
        }
    )
    repository = InMemoryPlayerRepository()
    app = create_app()
    app.dependency_overrides[get_season_dataset_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post("/ingestion/fbref/seasons/2026")

    assert response.status_code == 200
    assert response.json()["ingested"] == 1
    assert repository.get_player(1_500_000_000).birth_year == 2003


def test_ingest_understat_season_stores_advanced_metrics():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_season_statistics(
        1, Season("La Liga", "2026"), Statistics(7, 4, minutes_played=598), "Barcelona"
    )
    provider = FakeAdvancedSeasonProvider(
        {
            2026: [
                AdvancedSeasonRow(
                    competition="La Liga",
                    player=ExternalPlayer(
                        11500, "Lamine Yamal", ("Barcelona",), 598, 7
                    ),
                    advanced=AdvancedStatistics(6.08, 4.08, 27, 9.5, 2.1),
                )
            ]
        }
    )
    app = create_app()
    app.dependency_overrides[get_advanced_season_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    client = TestClient(app)

    response = client.post("/ingestion/understat/seasons/2026")

    assert response.status_code == 200
    assert response.json()["ingested"] == 1
    stats = repository.get_season_statistics(1, Season("La Liga", "2026"))
    assert stats.expected_assists == 4.08


def test_enrich_pending_players_enriches_up_to_the_limit():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Lamine Yamal", "Forward", None, birth_year=2007),
        Season("La Liga", "2026"),
        Statistics(7, 4),
    )
    provider = FakeMarketValueProvider(
        result=MarketValueHistoryResult(
            preferred_foot="left",
            points=[],
            photo_url="https://img.a.transfermarkt.technology/portrait/header/1.jpg",
        )
    )
    app = create_app()
    app.dependency_overrides[get_market_value_provider] = lambda: provider
    app.dependency_overrides[get_player_repository] = lambda: repository
    app.dependency_overrides[get_enrichment_pause] = lambda: lambda seconds: None
    client = TestClient(app)

    response = client.post("/ingestion/transfermarkt/enrich?limit=5")

    assert response.status_code == 200
    assert response.json()["ingested"] == 1
    assert repository.get_player(1).preferred_foot == "left"
