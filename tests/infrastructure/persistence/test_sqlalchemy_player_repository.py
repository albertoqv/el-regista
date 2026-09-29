import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="DATABASE_URL is not set; start Postgres with `docker compose up -d db`",
)


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


def test_saves_and_retrieves_a_player_with_its_statistics(session):
    repository = SqlAlchemyPlayerRepository(session)
    player = Player(1, "Player One", "Forward", date(1995, 1, 1))

    repository.save(player, Statistics(10, 5))
    retrieved_player, retrieved_stats = repository.get(1)

    assert retrieved_player == player
    assert retrieved_stats == Statistics(10, 5)


def test_get_returns_none_for_a_missing_player(session):
    repository = SqlAlchemyPlayerRepository(session)

    assert repository.get(999) is None


def test_save_updates_an_already_existing_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    player = Player(1, "Player One", "Forward", date(1995, 1, 1))
    repository.save(player, Statistics(10, 5))

    repository.save(player, Statistics(20, 15))

    _, updated_stats = repository.get(1)
    assert updated_stats == Statistics(20, 15)


def test_list_all_returns_every_saved_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save(Player(1, "Player One", "Forward", date(1995, 1, 1)), Statistics(10, 5))
    repository.save(Player(2, "Player Two", "Midfielder", date(1996, 1, 1)), Statistics(3, 3))

    entries = repository.list_all()

    assert {player.player_id for player, _ in entries} == {1, 2}
