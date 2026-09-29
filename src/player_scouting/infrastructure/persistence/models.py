from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PlayerModel(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    preferred_foot: Mapped[str | None] = mapped_column(String, nullable=True)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PlayerSeasonStatisticsModel(Base):
    __tablename__ = "player_season_statistics"
    __table_args__ = (UniqueConstraint("player_id", "competition", "season_label"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"), nullable=False
    )
    competition: Mapped[str] = mapped_column(String, nullable=False)
    season_label: Mapped[str] = mapped_column(String, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shots: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shots_on_target: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_goals: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    passes_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passes_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    key_passes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dribbles_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dribbles_attempted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tackles_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    interceptions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fouls_committed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fouls_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PlayerMarketValueModel(Base):
    __tablename__ = "player_market_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    club: Mapped[str] = mapped_column(String, nullable=False)


class LeagueIngestionJobModel(Base):
    __tablename__ = "league_ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(Integer, nullable=False)
    league_name: Mapped[str] = mapped_column(String, nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    next_page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
