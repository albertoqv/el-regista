from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from player_scouting.application.ports import LeaderMetric
from player_scouting.presentation.api.dependencies import PlayerRepositoryDep
from player_scouting.presentation.api.schemas import (
    SeasonLeaderOut,
    season_leader_out_from_domain,
)

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("/{start_year}/leaders", response_model=list[SeasonLeaderOut])
def list_season_leaders(
    start_year: int,
    repository: PlayerRepositoryDep,
    metric: LeaderMetric = "goals",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    competition: str | None = None,
) -> list[SeasonLeaderOut]:
    leaders = repository.list_season_leaders(
        str(start_year), metric, limit, competition
    )
    return [season_leader_out_from_domain(leader) for leader in leaders]
