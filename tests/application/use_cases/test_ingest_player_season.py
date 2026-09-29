from datetime import date

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.application.use_cases.ingest_player_season import (
    IngestPlayerSeasonUseCase,
)
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import (
    FakePlayerSeasonStatisticsProvider,
    InMemoryPlayerRepository,
)

PREMIER_LEAGUE_2023 = Season("Premier League", "2023")


def test_ingests_a_player_found_by_the_provider():
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
    use_case = IngestPlayerSeasonUseCase(provider, repository)

    result = use_case.execute("Haaland", league_id=39, season_year=2023)

    assert result.ingested == 1
    assert result.skipped == []
    player = repository.get_player(1)
    statistics = repository.get_season_statistics(1, PREMIER_LEAGUE_2023)
    assert player.name == "E. Haaland"
    assert player.date_of_birth == date(2000, 7, 21)
    assert statistics.goals == 36


def test_persists_the_player_photo():
    provider = FakePlayerSeasonStatisticsProvider(
        PlayerSeasonResult(
            player_id=1,
            name="E. Haaland",
            position="Attacker",
            date_of_birth=date(2000, 7, 21),
            season=PREMIER_LEAGUE_2023,
            statistics=Statistics(36, 8),
            photo_url="https://media.api-sports.io/football/players/1.png",
        )
    )
    repository = InMemoryPlayerRepository()
    use_case = IngestPlayerSeasonUseCase(provider, repository)

    use_case.execute("Haaland", league_id=39, season_year=2023)

    assert (
        repository.get_player(1).photo_url
        == "https://media.api-sports.io/football/players/1.png"
    )


def test_defaults_to_unknown_position_when_missing():
    provider = FakePlayerSeasonStatisticsProvider(
        PlayerSeasonResult(
            player_id=1,
            name="E. Haaland",
            position=None,
            date_of_birth=date(2000, 7, 21),
            season=PREMIER_LEAGUE_2023,
            statistics=Statistics(36, 8),
        )
    )
    repository = InMemoryPlayerRepository()
    use_case = IngestPlayerSeasonUseCase(provider, repository)

    use_case.execute("Haaland", league_id=39, season_year=2023)

    assert repository.get_player(1).position == "Unknown"


def test_reports_a_skipped_player_when_the_provider_finds_nothing():
    provider = FakePlayerSeasonStatisticsProvider(None)
    repository = InMemoryPlayerRepository()
    use_case = IngestPlayerSeasonUseCase(provider, repository)

    result = use_case.execute("Nobody", league_id=39, season_year=2023)

    assert result.ingested == 0
    assert len(result.skipped) == 1
    assert result.skipped[0].name == "Nobody"
