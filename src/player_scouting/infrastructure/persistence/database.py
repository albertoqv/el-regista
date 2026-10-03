from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from player_scouting.infrastructure.persistence.settings import get_settings

# pre_ping + recycle: connections survive the API or the database sleeping
# (Railway "serverless") instead of failing the first request after a pause.
_url = get_settings().database_url
engine = create_engine(
    _url,
    pool_pre_ping=True,
    pool_recycle=300,
    # Neon's pooler (PgBouncer, transaction mode) cannot keep psycopg's automatic
    # server-side prepared statements between transactions.
    connect_args={"prepare_threshold": None} if "-pooler." in _url else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
