import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import MatchStats
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_match_stats_repository import (  # noqa: E501
    SqlAlchemyMatchStatsRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="DATABASE_URL is not set")


@pytest.fixture
def session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


UPCOMING = MatchStats(
    "Premier League",
    "2026",
    date(2026, 10, 10),
    "Arsenal",
    "Leeds",
    "M Oliver",
    odds_home=1.4,
    odds_draw=4.8,
    odds_away=7.5,
)
PLAYED = MatchStats(
    "Premier League",
    "2026",
    date(2026, 10, 10),
    "Arsenal",
    "Leeds",
    "M Oliver",
    home_goals=2,
    away_goals=0,
    home_corners=7,
    away_corners=2,
    home_yellows=1,
    away_yellows=3,
    odds_home=1.38,
    odds_draw=5.0,
    odds_away=8.0,
)


def test_saves_upcoming_then_updates_it_when_played(session):
    repository = SqlAlchemyMatchStatsRepository(session)

    repository.save_match_stats([UPCOMING])
    assert (
        repository.find_upcoming(
            "Premier League", date(2026, 10, 10), "Arsenal", "Leeds"
        )
        == UPCOMING
    )

    repository.save_match_stats([PLAYED])
    [match] = repository.list_match_stats("Premier League", ["2026"])
    assert match == PLAYED
    assert repository.list_match_stats("La Liga", ["2026"]) == []
