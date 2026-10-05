import io
import os

import pytest
from sqlalchemy import text

from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.backup import dump_data, restore_data
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="DATABASE_URL is not set")


def _raw(session):
    return session.connection().connection.driver_connection


def test_the_dump_is_plain_copy_statements_that_psql_can_replay(session):
    SqlAlchemyPlayerRepository(session).save_player(
        Player(880001, "Pedri\tGonzález", "Midfielder", None)
    )
    session.flush()

    dump = b"".join(dump_data(_raw(session))).decode()

    assert 'COPY "players" (' in dump
    assert "Pedri\\tGonzález" in dump
    assert dump.count("\\.\n") == len(Base.metadata.sorted_tables)


def test_a_dump_restores_the_same_data(session):
    players = SqlAlchemyPlayerRepository(session)
    players.save_player(Player(880001, "Pedri", "Midfielder", None))
    players.save_season_statistics(
        880001, Season("La Liga", "2026"), Statistics(goals=3, assists=4)
    )
    session.flush()
    dump = b"".join(dump_data(_raw(session)))
    session.execute(text("DELETE FROM player_season_statistics"))
    session.execute(text("DELETE FROM players"))

    restore_data(_raw(session), io.BytesIO(dump))

    restored = players.get_season_statistics(880001, Season("La Liga", "2026"))
    assert restored is not None
    assert (restored.goals, restored.assists) == (3, 4)
    assert players.get_player(880001).name == "Pedri"
