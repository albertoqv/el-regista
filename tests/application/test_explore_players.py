from datetime import date

from player_scouting.application.use_cases.explore_players import (
    ExploreFilters,
    ExplorePlayersUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import InMemoryPlayerRepository

TODAY = date(2026, 9, 30)


def _add(repository, player_id, position, league, goals, minutes, born, value):
    repository.save_player(
        Player(player_id, f"P{player_id}", position, None, birth_year=born)
    )
    repository.save_season_statistics(
        player_id,
        Season(league, "2026"),
        Statistics(goals, 0, minutes_played=minutes),
        team=f"Team {player_id}",
    )
    if value:
        repository.save_market_value_history(
            player_id, [MarketValuePoint(date(2026, 6, 1), value, "x")]
        )


def _repository():
    repository = InMemoryPlayerRepository()
    _add(repository, 1, "Forward", "La Liga", 6, 600, 2004, 15_000_000)
    _add(repository, 2, "Forward", "La Liga", 8, 900, 1995, 60_000_000)
    _add(repository, 3, "Forward", "Serie A", 3, 200, 2005, 5_000_000)
    _add(repository, 4, "Midfielder", "La Liga", 9, 900, 2003, 20_000_000)
    return repository


def _explore(**filters):
    use_case = ExplorePlayersUseCase(_repository(), today=lambda: TODAY)
    return [
        row.record.player.player_id
        for row in use_case.execute(ExploreFilters(season_label="2026", **filters))
    ]


def test_filters_by_position_league_age_value_and_minutes():
    assert _explore(position="Forward", min_minutes=300) == [2, 1]
    assert _explore(position="Forward", competition="La Liga", max_age=23) == [1]
    assert _explore(max_value=16_000_000, min_minutes=0) == [1, 3]


def test_sorts_by_any_metric_in_totals_or_per_90():
    assert _explore(position="Forward", sort="goals", min_minutes=0) == [2, 1, 3]
    # Per 90: P1 0.9, P3 1.35, P2 0.8
    assert _explore(position="Forward", sort="goals", per_90=True, min_minutes=0) == [
        3,
        1,
        2,
    ]


def test_rows_carry_value_age_and_sort_value():
    use_case = ExplorePlayersUseCase(_repository(), today=lambda: TODAY)

    [row] = use_case.execute(ExploreFilters(season_label="2026", position="Midfielder"))

    assert row.market_value.amount_eur == 20_000_000
    assert row.age == 23
    assert row.sort_value == 9
