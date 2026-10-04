from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from player_scouting.application.ports import LeaderMetric, ShotMetric
from player_scouting.domain.season import BIG_FIVE
from player_scouting.infrastructure.persistence.overview import database_overview
from player_scouting.presentation.api.dependencies import (
    PlayerRepositoryDep,
    SessionDep,
    ShotRepositoryDep,
)
from player_scouting.presentation.api.schemas import (
    PartnershipOut,
    SeasonLeaderOut,
    ShotLeaderOut,
    partnership_out_from_domain,
    season_leader_out_from_domain,
    shot_leader_out_from_domain,
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
    # "All leagues" means the big five: the others have far fewer stats and would
    # crowd the boards with goals from much weaker leagues.
    leaders = repository.list_season_leaders(
        str(start_year),
        metric,
        limit,
        competition,
        competitions=None if competition else BIG_FIVE,
    )
    return [season_leader_out_from_domain(leader) for leader in leaders]


@router.get("/{start_year}/shot-leaders", response_model=list[ShotLeaderOut])
def list_shot_leaders(
    start_year: int,
    repository: ShotRepositoryDep,
    metric: ShotMetric = "late_goals",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    competition: str | None = None,
) -> list[ShotLeaderOut]:
    leaders = repository.list_shot_leaders(str(start_year), metric, limit, competition)
    return [shot_leader_out_from_domain(leader) for leader in leaders]


@router.get("/{start_year}/partnerships", response_model=list[PartnershipOut])
def list_partnerships(
    start_year: int,
    repository: ShotRepositoryDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    competition: str | None = None,
) -> list[PartnershipOut]:
    pairs = repository.list_partnerships(str(start_year), limit, competition)
    return [partnership_out_from_domain(pair) for pair in pairs]


overview_router = APIRouter(tags=["overview"])


@overview_router.get("/overview")
def overview(session: SessionDep) -> dict[str, int]:
    return database_overview(session)
