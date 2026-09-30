import pytest

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.use_cases.get_player_percentiles import (
    GetPlayerPercentilesUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import InMemoryPlayerRepository

LA_LIGA_2026 = Season("La Liga", "2026")


def _forward(repository, player_id, goals, minutes, position="Forward"):
    repository.add(
        Player(player_id, f"Player {player_id}", position, None, birth_year=2000),
        LA_LIGA_2026,
        Statistics(goals, 0, minutes_played=minutes),
    )


def test_ranks_against_same_position_peers_with_enough_minutes():
    repository = InMemoryPlayerRepository()
    _forward(repository, 1, goals=9, minutes=900)
    _forward(repository, 2, goals=1, minutes=900)
    _forward(repository, 3, goals=20, minutes=100)  # too few minutes
    _forward(repository, 4, goals=30, minutes=900, position="Defender")

    report = GetPlayerPercentilesUseCase(repository).execute(1, LA_LIGA_2026)

    assert report.position == "Forward"
    assert report.peer_count == 2
    assert report.minimum_minutes == 270
    assert report.metrics["goals"].percentile == 75


def test_the_player_is_ranked_even_below_the_minutes_threshold():
    repository = InMemoryPlayerRepository()
    _forward(repository, 1, goals=1, minutes=90)
    _forward(repository, 2, goals=5, minutes=900)

    report = GetPlayerPercentilesUseCase(repository).execute(1, LA_LIGA_2026)

    assert report.peer_count == 2


def test_unknown_player_season_raises():
    repository = InMemoryPlayerRepository()

    with pytest.raises(PlayerNotFoundError):
        GetPlayerPercentilesUseCase(repository).execute(1, LA_LIGA_2026)
