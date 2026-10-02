import os
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import Fixture, MatchRef
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.overview import (
    data_freshness,
    database_overview,
)
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_shot_repository import (
    SqlAlchemyShotRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_team_repository import (
    SqlAlchemyTeamRepository,
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


def test_counts_what_the_product_knows(session):
    before = database_overview(session)
    players = SqlAlchemyPlayerRepository(session)
    players.save_player(Player(1, "A", "Forward", None, photo_url="https://x/a.jpg"))
    players.save_season_statistics(1, Season("La Liga", "2026"), Statistics(1, 0))
    SqlAlchemyShotRepository(session).save_match(
        MatchRef(1, "La Liga", "2026", date(2026, 9, 1), "A", "B"), []
    )

    after = database_overview(session)

    assert after["players"] == before["players"] + 1
    assert after["players_with_photo"] == before["players_with_photo"] + 1
    assert after["player_seasons"] == before["player_seasons"] + 1
    assert after["matches_with_shots"] == before["matches_with_shots"] + 1
    assert {"shots", "competitions", "match_stats", "fixtures"} <= set(after)


def _fixture(match_id, kickoff, goals):
    return Fixture(
        match_id,
        "La Liga",
        "2031",
        kickoff,
        f"H{match_id}",
        f"A{match_id}",
        goals,
        goals,
        None,
        None,
    )


def test_finds_recent_matches_that_are_still_waiting_for_their_result(session):
    now = datetime(2031, 3, 20, 12)
    SqlAlchemyTeamRepository(session).save_team_season(
        [
            _fixture(990001, now - timedelta(days=5), None),
            _fixture(990002, now - timedelta(days=5), 1),
            _fixture(990003, now - timedelta(days=1), None),
            _fixture(990004, now - timedelta(days=40), None),
        ],
        [],
    )

    report = data_freshness(session, now)

    assert report.missing_results == ["H990001 - A990001 (La Liga, 2031-03-15)"]
    assert report.latest_result == now - timedelta(days=5)
