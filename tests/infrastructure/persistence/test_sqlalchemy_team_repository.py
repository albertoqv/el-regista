import os
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import Fixture, TeamMatch
from player_scouting.infrastructure.persistence.models import Base
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


def _fixture(match_id, day, played=True, league="La Liga"):
    return Fixture(
        match_id=match_id,
        competition=league,
        season_label="2026",
        kickoff=datetime(2026, 9, day, 21, 0),
        home_team="Barcelona",
        away_team="Getafe",
        home_goals=2 if played else None,
        away_goals=0 if played else None,
        home_xg=1.8 if played else None,
        away_xg=0.4 if played else None,
    )


def _team_match(match_id, team="Barcelona", opponent="Getafe", home=True):
    return TeamMatch(
        match_id=match_id,
        competition="La Liga",
        season_label="2026",
        played_on=date(2026, 9, 1),
        team=team,
        opponent=opponent,
        home=home,
        goals_for=2,
        goals_against=0,
        xg_for=1.8,
        xg_against=0.4,
        npxg_for=1.8,
        npxg_against=0.4,
        ppda=7.5,
        ppda_allowed=15.0,
        deep=12,
        deep_allowed=3,
        xpts=2.5,
        result="w",
    )


def test_saves_and_updates_fixtures_and_team_matches(session):
    repository = SqlAlchemyTeamRepository(session)

    repository.save_team_season([_fixture(1, 1, played=False)], [])
    repository.save_team_season(
        [_fixture(1, 1), _fixture(2, 20, played=False)], [_team_match(1)]
    )

    fixtures = repository.list_fixtures("La Liga")
    assert [(f.match_id, f.played) for f in fixtures] == [(1, True), (2, False)]
    [match] = repository.list_team_matches(["2026"])
    assert (match.team, match.ppda, match.xpts) == ("Barcelona", 7.5, 2.5)


def test_lists_fixtures_in_a_time_window(session):
    repository = SqlAlchemyTeamRepository(session)
    repository.save_team_season(
        [
            _fixture(1, 1),
            _fixture(2, 20, played=False),
            _fixture(3, 28, played=False, league="Serie A"),
        ],
        [],
    )

    window = repository.list_fixtures(
        start=datetime(2026, 9, 10), end=datetime(2026, 9, 30)
    )
    serie_a = repository.list_fixtures("Serie A")

    assert [f.match_id for f in window] == [2, 3]
    assert [f.match_id for f in serie_a] == [3]
