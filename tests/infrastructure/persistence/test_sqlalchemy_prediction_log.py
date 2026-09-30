import os
from dataclasses import replace
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import PredictionSnapshot
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_prediction_log import (
    SqlAlchemyPredictionLog,
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


SNAPSHOT = PredictionSnapshot(
    match_id=900001,
    competition="La Liga",
    season_label="2026",
    kickoff=datetime(2026, 10, 4, 21),
    home_team="Barcelona",
    away_team="Getafe",
    made_at=datetime(2026, 10, 2, 6),
    model=(0.7, 0.2, 0.1),
    market=None,
    over_2_5=0.55,
)


def test_saves_replaces_and_lists_snapshots(session):
    log = SqlAlchemyPredictionLog(session)

    log.save_snapshot(SNAPSHOT)
    later = replace(
        SNAPSHOT, made_at=datetime(2026, 10, 3, 6), market=(0.75, 0.15, 0.1)
    )
    log.save_snapshot(later)

    assert [s for s in log.list_snapshots() if s.match_id == 900001] == [later]
