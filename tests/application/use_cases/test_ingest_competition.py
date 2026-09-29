from datetime import date

from player_scouting.application.ports import (
    CompetitionStatisticsResult,
    PlayerCompetitionStats,
)
from player_scouting.application.use_cases.ingest_competition import (
    IngestCompetitionUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import (
    FakeBirthDateProvider,
    FakeCompetitionStatisticsProvider,
    InMemoryPlayerRepository,
)

WORLD_CUP_2018 = Season("FIFA World Cup", "2018")


def test_ingests_players_with_a_resolvable_birth_date():
    stats_provider = FakeCompetitionStatisticsProvider(
        CompetitionStatisticsResult(
            WORLD_CUP_2018,
            [PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5)],
        )
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    result = use_case.execute(competition_id=43, season_id=3)

    assert result.ingested == 1
    assert result.skipped == []
    player = repository.get_player(1)
    statistics = repository.get_season_statistics(1, WORLD_CUP_2018)
    assert player.name == "Player One"
    assert player.date_of_birth == date(1995, 1, 1)
    assert statistics.goals == 10
    assert statistics.assists == 5


def test_skips_players_without_a_resolvable_birth_date_and_reports_them():
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
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    result = use_case.execute(competition_id=43, season_id=3)

    assert result.ingested == 1
    assert len(result.skipped) == 1
    assert result.skipped[0].player_id == 2
    assert repository.get_player(2) is None


def test_persists_extended_metrics():
    stats_provider = FakeCompetitionStatisticsProvider(
        CompetitionStatisticsResult(
            WORLD_CUP_2018,
            [
                PlayerCompetitionStats(
                    1, "Player One", "Forward", "Argentina", 10, 5, shots=20
                ),
            ],
        )
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    use_case.execute(competition_id=43, season_id=3)

    statistics = repository.get_season_statistics(1, WORLD_CUP_2018)
    assert statistics.shots == 20


def test_defaults_to_unknown_position_when_missing():
    stats_provider = FakeCompetitionStatisticsProvider(
        CompetitionStatisticsResult(
            WORLD_CUP_2018,
            [PlayerCompetitionStats(1, "Player One", None, "Argentina", 10, 5)],
        )
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    use_case.execute(competition_id=43, season_id=3)

    player = repository.get_player(1)
    assert player.position == "Unknown"


def test_ingesting_the_same_competition_twice_does_not_overwrite_other_seasons():
    repository = InMemoryPlayerRepository()
    other_season = Season("FIFA World Cup", "2022")
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        other_season,
        Statistics(1, 1),
    )
    stats_provider = FakeCompetitionStatisticsProvider(
        CompetitionStatisticsResult(
            WORLD_CUP_2018,
            [PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5)],
        )
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    use_case.execute(competition_id=43, season_id=3)

    assert repository.get_season_statistics(1, other_season) == Statistics(1, 1)
    assert repository.get_season_statistics(1, WORLD_CUP_2018).goals == 10
