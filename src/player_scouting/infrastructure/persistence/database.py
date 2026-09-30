from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from player_scouting.infrastructure.persistence.settings import get_settings

# pre_ping + recycle: connections survive the API or the database sleeping
# (Railway "serverless") instead of failing the first request after a pause.
engine = create_engine(
    get_settings().database_url, pool_pre_ping=True, pool_recycle=300
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
