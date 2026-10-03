from player_scouting.application.player_matching import ExternalPlayer
from player_scouting.application.ports import AdvancedSeasonRow
from player_scouting.application.use_cases.ingest_advanced_season import (
    IngestAdvancedSeasonUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics
from tests.application.doubles import (
    FakeAdvancedSeasonProvider,
    InMemoryPlayerRepository,
)

LA_LIGA_2026 = Season("La Liga", "2026")
YAMAL_ADVANCED = AdvancedStatistics(
    expected_goals=6.08,
    expected_assists=4.08,
    key_passes=27,
    xg_chain=9.5,
    xg_buildup=2.1,
)


def _row(external_id: int, name: str, advanced=YAMAL_ADVANCED) -> AdvancedSeasonRow:
    return AdvancedSeasonRow(
        competition="La Liga",
        player=ExternalPlayer(
            external_id=external_id,
            name=name,
            teams=("Barcelona",),
            minutes=600,
            goals=7,
        ),
        advanced=advanced,
    )


def _repository_with_yamal() -> InMemoryPlayerRepository:
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_season_statistics(
        1, LA_LIGA_2026, Statistics(7, 4, minutes_played=600), team="Barcelona"
    )
    return repository


def test_stores_advanced_metrics_for_matched_players():
    repository = _repository_with_yamal()
    use_case = IngestAdvancedSeasonUseCase(
        FakeAdvancedSeasonProvider({2026: [_row(9001, "Lamine Yamal")]}), repository
    )

    result = use_case.execute(2026)

    assert result.ingested == 1
    stats = repository.get_season_statistics(1, LA_LIGA_2026)
    assert stats.expected_goals == 6.08
    assert stats.expected_assists == 4.08
    assert stats.key_passes == 27
    assert stats.goals == 7
    assert repository.understat_id_of(1) == 9001


def test_reports_players_that_could_not_be_matched():
    repository = _repository_with_yamal()
    use_case = IngestAdvancedSeasonUseCase(
        FakeAdvancedSeasonProvider(
            {2026: [_row(9001, "Lamine Yamal"), _row(9002, "Unknown Youngster")]}
        ),
        repository,
    )

    result = use_case.execute(2026)

    assert result.ingested == 1
    assert [s.name for s in result.skipped] == ["Unknown Youngster"]


def test_basic_refresh_afterwards_keeps_the_advanced_metrics():
    repository = _repository_with_yamal()
    IngestAdvancedSeasonUseCase(
        FakeAdvancedSeasonProvider({2026: [_row(9001, "Lamine Yamal")]}), repository
    ).execute(2026)

    repository.save_season_statistics(
        1, LA_LIGA_2026, Statistics(8, 4, minutes_played=690), team="Barcelona"
    )

    stats = repository.get_season_statistics(1, LA_LIGA_2026)
    assert stats.goals == 8
    assert stats.expected_goals == 6.08


def _united_player(player_id, name, fbref_team="Manchester Utd"):
    return (
        Player(player_id, name, "Forward", None, birth_year=2000),
        fbref_team,
    )


def test_learns_understat_team_names_and_uses_them_everywhere():
    repository = InMemoryPlayerRepository()
    premier = Season("Premier League", "2026")
    players = [
        _united_player(1, "Bruno Fernandes"),
        _united_player(2, "Amad Diallo"),
        _united_player(3, "Kobbie Mainoo"),
        _united_player(4, "Moved Midfielder", "Manchester Utd, Everton"),
    ]
    for player, team in players:
        repository.save_player(player)
        repository.save_season_statistics(
            player.player_id, premier, Statistics(1, 0, minutes_played=500), team=team
        )
    rows = [
        AdvancedSeasonRow(
            competition="Premier League",
            player=ExternalPlayer(
                9000 + p.player_id, p.name, ("Manchester United",), 500, 1
            ),
            advanced=YAMAL_ADVANCED,
        )
        for p, _ in players[:3]
    ]

    IngestAdvancedSeasonUseCase(
        FakeAdvancedSeasonProvider({2026: rows}), repository
    ).execute(2026)

    assert repository.get_season_team(1, premier) == "Manchester United"
    # The FBref name inside a two-club season is renamed too.
    assert repository.get_season_team(4, premier) == "Manchester United, Everton"


def test_one_odd_player_does_not_rename_a_team():
    repository = _repository_with_yamal()
    row = AdvancedSeasonRow(
        competition="La Liga",
        player=ExternalPlayer(9001, "Lamine Yamal", ("Real Madrid",), 600, 7),
        advanced=YAMAL_ADVANCED,
    )

    IngestAdvancedSeasonUseCase(
        FakeAdvancedSeasonProvider({2026: [row]}), repository
    ).execute(2026)

    assert repository.get_season_team(1, LA_LIGA_2026) == "Barcelona"
