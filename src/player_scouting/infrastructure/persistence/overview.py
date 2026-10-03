from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.orm import Session

from player_scouting.infrastructure.persistence.models import (
    FixtureModel,
    MatchStatsModel,
    PlayerModel,
    PlayerSeasonStatisticsModel,
    RosterModel,
    ShotModel,
    UnderstatMatchModel,
)


def database_overview(session: Session) -> dict[str, int]:
    """Headline numbers for the product: what the data actually covers."""

    def count(statement: Select[Any]) -> int:
        return int(session.execute(statement).scalar() or 0)

    return {
        "players": count(select(func.count()).select_from(PlayerModel)),
        "players_with_photo": count(
            select(func.count())
            .select_from(PlayerModel)
            .where(PlayerModel.photo_url.is_not(None))
        ),
        "player_seasons": count(
            select(func.count()).select_from(PlayerSeasonStatisticsModel)
        ),
        "competitions": count(
            select(func.count(distinct(PlayerSeasonStatisticsModel.competition)))
        ),
        "matches_with_shots": count(
            select(func.count()).select_from(UnderstatMatchModel)
        ),
        "shots": count(select(func.count()).select_from(ShotModel)),
        "match_stats": count(select(func.count()).select_from(MatchStatsModel)),
        "fixtures": count(select(func.count()).select_from(FixtureModel)),
    }


# A result can take a couple of days to reach Understat; after that it is a failure.
RESULT_GRACE = timedelta(days=3)
# Older gaps are postponed matches waiting for a new date, not a broken refresh.
RESULT_WINDOW = timedelta(days=14)


# One goal apart is a source a day behind the other, not an error.
GOAL_TOLERANCE = 1


@dataclass(frozen=True)
class DataFreshness:
    missing_results: list[str]
    latest_result: datetime | None
    goal_mismatches: list[str] = field(default_factory=list)


def goal_mismatches(session: Session, season_label: str) -> list[str]:
    """Players whose season goals differ between FBref and Understat's matches."""
    understat = (
        select(
            RosterModel.understat_player_id.label("understat_id"),
            RosterModel.competition.label("competition"),
            func.sum(RosterModel.goals).label("goals"),
        )
        .where(RosterModel.season_label == season_label)
        .group_by(RosterModel.understat_player_id, RosterModel.competition)
        .subquery()
    )
    rows = session.execute(
        select(
            PlayerModel.name,
            PlayerSeasonStatisticsModel.competition,
            PlayerSeasonStatisticsModel.goals,
            understat.c.goals,
        )
        .join(
            PlayerModel, PlayerModel.player_id == PlayerSeasonStatisticsModel.player_id
        )
        .join(
            understat,
            (understat.c.understat_id == PlayerModel.understat_id)
            & (understat.c.competition == PlayerSeasonStatisticsModel.competition),
        )
        .where(
            PlayerSeasonStatisticsModel.season_label == season_label,
            func.abs(PlayerSeasonStatisticsModel.goals - understat.c.goals)
            > GOAL_TOLERANCE,
        )
        .order_by(PlayerModel.name)
    ).all()
    return [
        f"{name} ({competition}): FBref {fbref}, Understat {int(other)}"
        for name, competition, fbref, other in rows
    ]


def data_freshness(session: Session, now: datetime) -> DataFreshness:
    """Matches played a few days ago that still have no score: the refresh broke."""
    missing = session.scalars(
        select(FixtureModel)
        .where(
            FixtureModel.home_goals.is_(None),
            FixtureModel.kickoff < now - RESULT_GRACE,
            FixtureModel.kickoff >= now - RESULT_WINDOW,
        )
        .order_by(FixtureModel.kickoff)
    ).all()
    latest = session.execute(
        select(func.max(FixtureModel.kickoff)).where(
            FixtureModel.home_goals.is_not(None), FixtureModel.kickoff <= now
        )
    ).scalar()
    return DataFreshness(
        missing_results=[
            f"{f.home_team} - {f.away_team} ({f.competition}, {f.kickoff.date()})"
            for f in missing
        ],
        latest_result=latest,
    )
