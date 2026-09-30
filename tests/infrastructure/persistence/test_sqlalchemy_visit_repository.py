import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import DailyVisits, PageView
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_visit_repository import (
    SqlAlchemyVisitRepository,
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


def test_aggregates_views_and_daily_unique_visitors(session):
    repository = SqlAlchemyVisitRepository(session)
    for day, path, visitor, referrer in [
        (date(2026, 9, 29), "/", "a", None),
        (date(2026, 9, 30), "/", "a", "google.com"),
        (date(2026, 9, 30), "/gemelos", "a", "google.com"),
        (date(2026, 9, 30), "/", "b", "t.co"),
        (date(2026, 8, 1), "/", "old", None),
    ]:
        repository.save_page_view(PageView(day, path, visitor, referrer))

    since = date(2026, 9, 1)

    assert repository.daily_visits(since) == [
        DailyVisits(date(2026, 9, 29), 1, 1),
        DailyVisits(date(2026, 9, 30), 3, 2),
    ]
    pages = repository.top_pages(since, 10)
    assert [(p.name, p.views, p.visitors) for p in pages] == [
        ("/", 3, 3),  # visitors are counted per day
        ("/gemelos", 1, 1),
    ]
    referrers = repository.top_referrers(since, 1)
    assert [(r.name, r.views) for r in referrers] == [("google.com", 2)]
