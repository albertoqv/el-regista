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
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)


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
