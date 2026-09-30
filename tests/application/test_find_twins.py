from datetime import date

import pytest

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.use_cases.find_twins import (
    FindTwinsUseCase,
    TwinFilters,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import InMemoryPlayerRepository

LA_LIGA_2025 = Season("La Liga", "2025")
SERIE_A_2025 = Season("Serie A", "2025")
TODAY = date(2026, 9, 30)


def _stats(goals: int, assists: int, shots: int, tackles: int, minutes: int = 2700):
    return Statistics(
        goals,
        assists,
        shots=shots,
        shots_on_target=shots // 3,
        key_passes=assists * 3,
        tackles_won=tackles,
        interceptions=tackles // 2,
        fouls_won=10,
        minutes_played=minutes,
    )


def _add(
    repository,
    player_id,
    name,
    season,
    stats,
    position="Forward",
    value=None,
    born=2000,
):
    repository.save_player(Player(player_id, name, position, None, birth_year=born))
    repository.save_season_statistics(
        player_id, season, stats, team=f"Team {player_id}"
    )
    if value is not None:
        repository.save_market_value_history(
            player_id, [MarketValuePoint(date(2026, 6, 1), value, f"Team {player_id}")]
        )


def _repository():
    repository = InMemoryPlayerRepository()
    _add(
        repository,
        1,
        "Star",
        LA_LIGA_2025,
        _stats(20, 10, 100, 10),
        value=200_000_000,
        born=2007,
    )
    _add(
        repository,
        2,
        "Twin",
        LA_LIGA_2025,
        _stats(19, 10, 98, 11),
        value=40_000_000,
        born=2001,
    )
    _add(
        repository,
        3,
        "Italian twin",
        SERIE_A_2025,
        _stats(20, 9, 100, 12),
        value=25_000_000,
        born=1995,
    )
    _add(repository, 4, "Poacher", LA_LIGA_2025, _stats(25, 0, 60, 2), value=10_000_000)
    _add(repository, 5, "Bench", LA_LIGA_2025, _stats(5, 1, 20, 1, minutes=300))
    _add(
        repository,
        6,
        "Defender",
        LA_LIGA_2025,
        _stats(0, 1, 5, 80),
        position="Defender",
    )
    _add(repository, 7, "Grinder", LA_LIGA_2025, _stats(2, 1, 20, 60))
    _add(repository, 8, "Italian grinder", SERIE_A_2025, _stats(3, 2, 25, 55))
    return repository


def _use_case(repository):
    return FindTwinsUseCase(repository, today=lambda: TODAY)


def test_twins_are_same_position_players_ranked_by_style_similarity():
    report = _use_case(_repository()).execute(1)

    names = [twin.player.name for twin in report.twins]
    assert names[:2] == ["Twin", "Italian twin"] or names[:2] == [
        "Italian twin",
        "Twin",
    ]
    assert "Defender" not in names
    assert "Star" not in names
    assert report.target.season == LA_LIGA_2025
    assert report.target.market_value.amount_eur == 200_000_000


def test_players_with_too_few_minutes_are_not_twins():
    report = _use_case(_repository()).execute(1)

    assert "Bench" not in [twin.player.name for twin in report.twins]


def test_twins_carry_price_team_and_what_makes_them_alike():
    report = _use_case(_repository()).execute(1)
    twin = next(twin for twin in report.twins if twin.player.name == "Twin")
    poacher = next(twin for twin in report.twins if twin.player.name == "Poacher")

    assert twin.market_value.amount_eur == 40_000_000
    assert twin.team == "Team 2"
    assert twin.similarity > poacher.similarity
    assert len(twin.shared_strengths) > 0


def test_filters_by_budget_age_and_league():
    use_case = _use_case(_repository())

    cheap = use_case.execute(1, filters=TwinFilters(max_value=30_000_000))
    young = use_case.execute(1, filters=TwinFilters(max_age=26))
    italian = use_case.execute(1, filters=TwinFilters(competition="Serie A"))

    assert [t.player.name for t in cheap.twins][0] == "Italian twin"
    assert all(
        t.market_value and t.market_value.amount_eur <= 30_000_000 for t in cheap.twins
    )
    assert "Italian twin" not in [t.player.name for t in young.twins]
    assert {t.season.competition for t in italian.twins} == {"Serie A"}


def test_unknown_player_raises():
    with pytest.raises(PlayerNotFoundError):
        _use_case(_repository()).execute(999)
