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
