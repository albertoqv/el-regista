from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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
    understat_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transfermarkt_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, unique=True
    )
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detailed_position: Mapped[str | None] = mapped_column(String, nullable=True)
    enrichment_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


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
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    team: Mapped[str | None] = mapped_column(String, nullable=True)


class PlayerSeasonAdvancedStatisticsModel(Base):
    __tablename__ = "player_season_advanced_stats"
    __table_args__ = (UniqueConstraint("player_id", "competition", "season_label"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"), nullable=False
    )
    competition: Mapped[str] = mapped_column(String, nullable=False)
    season_label: Mapped[str] = mapped_column(String, nullable=False)
    expected_goals: Mapped[float] = mapped_column(Float, nullable=False)
    expected_assists: Mapped[float] = mapped_column(Float, nullable=False)
    key_passes: Mapped[int] = mapped_column(Integer, nullable=False)
    xg_chain: Mapped[float] = mapped_column(Float, nullable=False)
    xg_buildup: Mapped[float] = mapped_column(Float, nullable=False)


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


class UnderstatMatchModel(Base):
    __tablename__ = "understat_matches"

    match_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    competition: Mapped[str] = mapped_column(String, nullable=False)
    season_label: Mapped[str] = mapped_column(String, nullable=False, index=True)
    played_on: Mapped[date] = mapped_column(Date, nullable=False)
    home_team: Mapped[str] = mapped_column(String, nullable=False)
    away_team: Mapped[str] = mapped_column(String, nullable=False)


class ShotModel(Base):
    __tablename__ = "shots"

    shot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("understat_matches.match_id"), nullable=False, index=True
    )
    understat_player_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    player_name: Mapped[str] = mapped_column(String, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    xg: Mapped[float] = mapped_column(Float, nullable=False)
    situation: Mapped[str] = mapped_column(String, nullable=False)
    shot_type: Mapped[str] = mapped_column(String, nullable=False)
    home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    assisted_by: Mapped[str | None] = mapped_column(String, nullable=True)
    decisive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outside_box: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class FixtureModel(Base):
    __tablename__ = "fixtures"

    match_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    competition: Mapped[str] = mapped_column(String, nullable=False, index=True)
    season_label: Mapped[str] = mapped_column(String, nullable=False)
    kickoff: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    home_team: Mapped[str] = mapped_column(String, nullable=False)
    away_team: Mapped[str] = mapped_column(String, nullable=False)
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_xg: Mapped[float | None] = mapped_column(Float, nullable=True)


class TeamMatchModel(Base):
    __tablename__ = "team_matches"

    match_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    team: Mapped[str] = mapped_column(String, primary_key=True)
    competition: Mapped[str] = mapped_column(String, nullable=False)
    season_label: Mapped[str] = mapped_column(String, nullable=False, index=True)
    played_on: Mapped[date] = mapped_column(Date, nullable=False)
    opponent: Mapped[str] = mapped_column(String, nullable=False)
    home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False)
    xg_for: Mapped[float] = mapped_column(Float, nullable=False)
    xg_against: Mapped[float] = mapped_column(Float, nullable=False)
    npxg_for: Mapped[float] = mapped_column(Float, nullable=False)
    npxg_against: Mapped[float] = mapped_column(Float, nullable=False)
    ppda: Mapped[float | None] = mapped_column(Float, nullable=True)
    ppda_allowed: Mapped[float | None] = mapped_column(Float, nullable=True)
    deep: Mapped[int] = mapped_column(Integer, nullable=False)
    deep_allowed: Mapped[int] = mapped_column(Integer, nullable=False)
    xpts: Mapped[float] = mapped_column(Float, nullable=False)
    result: Mapped[str] = mapped_column(String, nullable=False)
