import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from player_scouting.infrastructure.persistence.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL")


@pytest.fixture
def session():
    """A session on empty tables, whatever the database already holds.

    Everything runs in one transaction that is rolled back at the end: the
    TRUNCATE included (it is transactional in Postgres), so a developer's local
    data is back untouched after the test.
    """
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    tables = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    connection.execute(text(f"TRUNCATE {tables} CASCADE"))
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()
