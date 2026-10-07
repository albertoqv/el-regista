import os
from dataclasses import replace
from datetime import date

import pytest

from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
from player_scouting.infrastructure.persistence.sqlalchemy_competition_stats_repository import (  # noqa: E501
    SqlAlchemyCompetitionStatsRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="DATABASE_URL is not set")

CHAMPIONS = CompetitionLine(
    competition="Champions League",
    kind="continental",
    season_label="2025",
    team="FC Barcelona",
    appearances=10,
    goals=6,
    assists=4,
    minutes_played=874,
    yellow_cards=1,
    red_cards=0,
)
LEAGUE = replace(CHAMPIONS, competition="La Liga", kind="league", appearances=28)
WORLD_CUP = replace(
    CHAMPIONS, competition="Mundial", kind="national", season_label="2026", team="Spain"
)


def _players(session):
    players = SqlAlchemyPlayerRepository(session)
    for player_id in (1, 2):
        players.save_player(
            Player(player_id, f"P{player_id}", "Forward", date(2007, 7, 13))
        )


def test_saves_lines_in_bulk_and_lists_them_newest_first(session):
    _players(session)
    repository = SqlAlchemyCompetitionStatsRepository(session)

    repository.save_competition_lines({1: [CHAMPIONS, WORLD_CUP, LEAGUE], 2: [LEAGUE]})

    assert repository.list_competition_lines(1) == [WORLD_CUP, LEAGUE, CHAMPIONS]
    assert repository.list_competition_lines(2) == [LEAGUE]


def test_saving_the_same_competition_and_season_again_replaces_it(session):
    _players(session)
    repository = SqlAlchemyCompetitionStatsRepository(session)
    repository.save_competition_lines({1: [CHAMPIONS]})

    later = replace(CHAMPIONS, appearances=12, goals=8)
    repository.save_competition_lines({1: [later]})

    assert repository.list_competition_lines(1) == [later]


def test_the_age_benchmark_averages_one_position_at_each_age(session):
    players = SqlAlchemyPlayerRepository(session)
    players.save_player(Player(1, "A", "Forward", date(2005, 3, 1)))
    players.save_player(Player(2, "B", "Forward", None, birth_year=2005))
    players.save_player(Player(3, "C", "Defender", date(2005, 3, 1)))
    players.save_player(Player(4, "D", "Forward", date(2000, 3, 1)))
    repository = SqlAlchemyCompetitionStatsRepository(session)
    season = replace(LEAGUE, season_label="2024", minutes_played=1800)
    repository.save_competition_lines(
        {
            1: [replace(season, goals=10, assists=0)],
            # Two competitions of one season count as one season.
            2: [
                replace(season, goals=2, assists=0, minutes_played=900),
                replace(
                    CHAMPIONS,
                    season_label="2024",
                    goals=4,
                    assists=0,
                    minutes_played=900,
                ),
            ],
            3: [replace(season, goals=30, assists=0)],
            # Too few minutes to tell his level.
            4: [replace(season, goals=9, assists=0, minutes_played=300)],
        }
    )

    [nineteen] = repository.age_benchmark("Forward")

    assert (nineteen.age, nineteen.players) == (19, 2)
    assert nineteen.per90 == round((10 + 6) * 90 / 3600, 3)
