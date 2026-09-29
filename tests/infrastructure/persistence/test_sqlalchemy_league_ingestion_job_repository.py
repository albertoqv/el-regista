import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_league_ingestion_job_repository import (  # noqa: E501
    SqlAlchemyLeagueIngestionJobRepository,
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


def test_saving_a_new_job_assigns_it_an_id(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)
    job = LeagueIngestionJob(
        id=None, league_id=140, league_name="La Liga", season_year=2023
    )

    saved = repository.save_job(job)

    assert saved.id is not None
    assert repository.get_job(saved.id) == saved


def test_saving_an_existing_job_updates_it_instead_of_duplicating(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)
    job = repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )

    repository.save_job(
        LeagueIngestionJob(
            id=job.id,
            league_id=140,
            league_name="La Liga",
            season_year=2023,
            next_page=2,
            total_pages=45,
        )
    )

    updated = repository.get_job(job.id)
    assert updated.next_page == 2
    assert updated.total_pages == 45
    assert len(repository.list_jobs()) == 1


def test_get_job_returns_none_for_a_missing_job(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)

    assert repository.get_job(999) is None


def test_next_pending_job_returns_the_first_incomplete_job_by_creation_order(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)
    first = repository.save_job(
        LeagueIngestionJob(
            id=None,
            league_id=140,
            league_name="La Liga",
            season_year=2023,
            next_page=3,
            total_pages=2,
        )
    )
    second = repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=39, league_name="Premier League", season_year=2023
        )
    )

    pending = repository.next_pending_job()

    assert pending.id == second.id
    assert first.id != pending.id


def test_next_pending_job_returns_none_when_every_job_is_completed(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)
    repository.save_job(
        LeagueIngestionJob(
            id=None,
            league_id=140,
            league_name="La Liga",
            season_year=2023,
            next_page=3,
            total_pages=2,
        )
    )

    assert repository.next_pending_job() is None


def test_lists_every_job(session):
    repository = SqlAlchemyLeagueIngestionJobRepository(session)
    repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=39, league_name="Premier League", season_year=2023
        )
    )

    jobs = repository.list_jobs()

    assert {(job.league_id, job.season_year) for job in jobs} == {
        (140, 2023),
        (39, 2023),
    }
