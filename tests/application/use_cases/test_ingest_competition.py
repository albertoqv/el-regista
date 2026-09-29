from datetime import date

from player_scouting.application.ports import PlayerCompetitionStats
from player_scouting.application.use_cases.ingest_competition import (
    IngestCompetitionUseCase,
)
from tests.application.doubles import (
    FakeBirthDateProvider,
    FakeCompetitionStatisticsProvider,
    InMemoryPlayerRepository,
)


def test_ingests_players_with_a_resolvable_birth_date():
    stats_provider = FakeCompetitionStatisticsProvider(
        [
            PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5),
        ]
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    result = use_case.execute(competition_id=43, season_id=3)

    assert result.ingested == 1
    assert result.skipped == []
    player, statistics = repository.get(1)
    assert player.name == "Player One"
    assert player.date_of_birth == date(1995, 1, 1)
    assert statistics.goals == 10
    assert statistics.assists == 5


def test_skips_players_without_a_resolvable_birth_date_and_reports_them():
    stats_provider = FakeCompetitionStatisticsProvider(
        [
            PlayerCompetitionStats(1, "Player One", "Forward", "Argentina", 10, 5),
            PlayerCompetitionStats(2, "Unknown Player", "Midfielder", None, 1, 1),
        ]
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    result = use_case.execute(competition_id=43, season_id=3)

    assert result.ingested == 1
    assert len(result.skipped) == 1
    assert result.skipped[0].player_id == 2
    assert repository.get(2) is None


def test_persists_extended_metrics():
    stats_provider = FakeCompetitionStatisticsProvider(
        [
            PlayerCompetitionStats(
                1, "Player One", "Forward", "Argentina", 10, 5, shots=20
            ),
        ]
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    use_case.execute(competition_id=43, season_id=3)

    _, statistics = repository.get(1)
    assert statistics.shots == 20


def test_defaults_to_unknown_position_when_missing():
    stats_provider = FakeCompetitionStatisticsProvider(
        [PlayerCompetitionStats(1, "Player One", None, "Argentina", 10, 5)]
    )
    birth_date_provider = FakeBirthDateProvider({"Player One": date(1995, 1, 1)})
    repository = InMemoryPlayerRepository()
    use_case = IngestCompetitionUseCase(stats_provider, birth_date_provider, repository)

    use_case.execute(competition_id=43, season_id=3)

    player, _ = repository.get(1)
    assert player.position == "Unknown"
