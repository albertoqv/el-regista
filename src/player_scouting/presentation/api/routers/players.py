from __future__ import annotations

from fastapi import APIRouter, HTTPException

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.presentation.api.dependencies import (
    ComparePlayersUseCaseDep,
    FindSimilarPlayersUseCaseDep,
    PlayerRepositoryDep,
)
from player_scouting.presentation.api.schemas import (
    ComparisonOut,
    PlayerOut,
    comparison_out_from_domain,
    player_out_from_domain,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, repository: PlayerRepositoryDep) -> PlayerOut:
    entry = repository.get(player_id)
    if entry is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    player, statistics = entry
    return player_out_from_domain(player, statistics)


@router.get("/{player_id_a}/compare/{player_id_b}", response_model=ComparisonOut)
def compare_players(
    player_id_a: int,
    player_id_b: int,
    use_case: ComparePlayersUseCaseDep,
) -> ComparisonOut:
    try:
        comparison = use_case.execute(player_id_a, player_id_b)
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return comparison_out_from_domain(comparison)


@router.get("/{player_id}/similar", response_model=list[ComparisonOut])
def find_similar_players(
    player_id: int,
    use_case: FindSimilarPlayersUseCaseDep,
    top: int = 5,
) -> list[ComparisonOut]:
    try:
        comparisons = use_case.execute(player_id, top_n=top)
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [comparison_out_from_domain(comparison) for comparison in comparisons]
