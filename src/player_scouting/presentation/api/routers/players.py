from __future__ import annotations

from fastapi import APIRouter, HTTPException

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.domain.season import Season
from player_scouting.presentation.api.dependencies import (
    ComparePlayersUseCaseDep,
    FindSimilarPlayersUseCaseDep,
    PlayerRepositoryDep,
)
from player_scouting.presentation.api.schemas import (
    ComparisonOut,
    PlayerOut,
    SeasonOut,
    SimilarPlayerMatchOut,
    comparison_out_from_domain,
    player_out_from_domain,
    season_out_from_domain,
    similar_player_match_out_from_domain,
)

router = APIRouter(prefix="/players", tags=["players"])


def _season_or_none(competition: str | None, label: str | None) -> Season | None:
    if competition is None or label is None:
        return None
    return Season(competition, label)


@router.get("", response_model=list[PlayerOut])
def list_players(repository: PlayerRepositoryDep) -> list[PlayerOut]:
    return [
        player_out_from_domain(
            player, repository.get_career_statistics(player.player_id)
        )
        for player in repository.list_players()
    ]


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, repository: PlayerRepositoryDep) -> PlayerOut:
    player = repository.get_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    statistics = repository.get_career_statistics(player_id)
    return player_out_from_domain(player, statistics)


@router.get("/{player_id}/seasons", response_model=list[SeasonOut])
def list_player_seasons(
    player_id: int, repository: PlayerRepositoryDep
) -> list[SeasonOut]:
    player = repository.get_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    return [
        season_out_from_domain(season)
        for season in repository.list_seasons_for_player(player_id)
    ]


@router.get("/{player_id}/seasons/{competition}/{label}", response_model=PlayerOut)
def get_player_season(
    player_id: int, competition: str, label: str, repository: PlayerRepositoryDep
) -> PlayerOut:
    player = repository.get_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    season = Season(competition, label)
    statistics = repository.get_season_statistics(player_id, season)
    if statistics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No statistics found for player {player_id} in {season}",
        )
    return player_out_from_domain(player, statistics)


@router.get("/{player_id_a}/compare/{player_id_b}", response_model=ComparisonOut)
def compare_players(
    player_id_a: int,
    player_id_b: int,
    use_case: ComparePlayersUseCaseDep,
    season_a_competition: str | None = None,
    season_a_label: str | None = None,
    season_b_competition: str | None = None,
    season_b_label: str | None = None,
) -> ComparisonOut:
    try:
        comparison = use_case.execute(
            player_id_a,
            player_id_b,
            season_a=_season_or_none(season_a_competition, season_a_label),
            season_b=_season_or_none(season_b_competition, season_b_label),
        )
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return comparison_out_from_domain(comparison)


@router.get("/{player_id}/similar", response_model=list[SimilarPlayerMatchOut])
def find_similar_players(
    player_id: int,
    use_case: FindSimilarPlayersUseCaseDep,
    top: int = 5,
    season_competition: str | None = None,
    season_label: str | None = None,
) -> list[SimilarPlayerMatchOut]:
    try:
        matches = use_case.execute(
            player_id,
            season=_season_or_none(season_competition, season_label),
            top_n=top,
        )
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [similar_player_match_out_from_domain(match) for match in matches]
