from __future__ import annotations

from typing import Any

from sqlalchemy import Select, distinct, func, select
from sqlalchemy.orm import Session

from player_scouting.infrastructure.persistence.models import (
    FixtureModel,
    MatchStatsModel,
    PlayerModel,
    PlayerSeasonStatisticsModel,
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
