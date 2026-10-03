from __future__ import annotations

import time
from dataclasses import asdict
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerSort
from player_scouting.application.use_cases.explore_players import (
    ExploreFilters,
    ExploreSort,
)
from player_scouting.application.use_cases.find_twins import TwinFilters
from player_scouting.application.use_cases.hot_players import (
    HotMetric,
    HotPlayersUseCase,
)
from player_scouting.domain.season import Season
from player_scouting.infrastructure.understat.provider import LEAGUES
from player_scouting.presentation.api.dependencies import (
    ComparePlayersUseCaseDep,
    ExplorePlayersUseCaseDep,
    FindSimilarPlayersUseCaseDep,
    FindTwinsUseCaseDep,
    GetPlayerPercentilesUseCaseDep,
    PlayerRepositoryDep,
    ShotRepositoryDep,
)
from player_scouting.presentation.api.schemas import (
    ComparisonOut,
    ExploreRowOut,
    MarketValueHistoryOut,
    PercentileReportOut,
    PlayerOut,
    PlayerShotOut,
    SeasonOut,
    SimilarPlayerMatchOut,
    TwinReportOut,
    comparison_out_from_domain,
    explore_row_out_from_domain,
    market_value_history_out_from_domain,
    percentile_report_out_from_domain,
    player_out_from_domain,
    player_shot_out_from_domain,
    season_out_from_domain,
    similar_player_match_out_from_domain,
    twin_report_out_from_domain,
)

router = APIRouter(prefix="/players", tags=["players"])


def _season_or_none(competition: str | None, label: str | None) -> Season | None:
    if competition is None or label is None:
        return None
    return Season(competition, label)


@router.get("", response_model=list[PlayerOut])
def list_players(
    repository: PlayerRepositoryDep,
    q: str | None = None,
    sort: PlayerSort = "recent",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PlayerOut]:
    return [
        player_out_from_domain(
            summary.player, summary.career, summary.latest_season_year
        )
        for summary in repository.search_player_summaries(q, sort, limit)
    ]


def _current_season_label() -> str:
    """The season being played: it starts in July."""
    today = date.today()
    return str(today.year if today.month >= 7 else today.year - 1)


@router.get("/explore", response_model=list[ExploreRowOut])
def explore_players(
    use_case: ExplorePlayersUseCaseDep,
    season: str | None = None,
    competition: str | None = None,
    position: str | None = None,
    min_age: Annotated[int | None, Query(ge=14, le=50)] = None,
    max_age: Annotated[int | None, Query(ge=14, le=50)] = None,
    max_value: Annotated[int | None, Query(ge=0)] = None,
    min_minutes: Annotated[int, Query(ge=0)] = 0,
    sort: ExploreSort = "goals",
    per_90: bool = False,
    ascending: bool = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ExploreRowOut]:
    rows = use_case.execute(
        ExploreFilters(
            season_label=season or _current_season_label(),
            competition=competition,
            position=position,
            min_age=min_age,
            max_age=max_age,
            max_value=max_value,
            min_minutes=min_minutes,
            sort=sort,
            per_90=per_90,
            ascending=ascending,
            limit=limit,
        )
    )
    return [explore_row_out_from_domain(row) for row in rows]


# Replaced in tests: "the last N days" are counted back from today.
_today = date.today
HOT_CACHE_SECONDS = 600
_hot_cache: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}


@router.get("/hot")
def hot_players(
    shots: ShotRepositoryDep,
    players: PlayerRepositoryDep,
    season: str | None = None,
    competition: str | None = None,
    metric: HotMetric = "goals_assists",
    days: Annotated[int, Query(ge=7, le=90)] = 30,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> dict[str, Any]:
    """Who is on fire lately (Understat lineups, the five big leagues)."""
    key = (season, competition, metric, days, limit, _today())
    cached = _hot_cache.get(key)
    if cached and time.monotonic() - cached[0] < HOT_CACHE_SECONDS:
        return cached[1]
    board = HotPlayersUseCase(shots, list(LEAGUES.values()), _today).execute(
        season or _current_season_label(),
        days=days,
        metric=metric,
        limit=limit,
        competition=competition,
    )
    known = players.find_by_understat_ids(
        [p.understat_player_id for p in board.players]
    )
    rows = []
    for hot in board.players:
        row = asdict(hot)
        player = known.get(hot.understat_player_id)
        row["player_id"] = player.player_id if player else None
        row["photo_url"] = player.photo_url if player else None
        if player:
            row["name"] = player.name
        rows.append(row)
    body = {
        "window_start": board.window_start.isoformat(),
        "window_end": board.window_end.isoformat(),
        "metric": board.metric,
        "players": rows,
    }
    _hot_cache[key] = (time.monotonic(), body)
    return body


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, repository: PlayerRepositoryDep) -> PlayerOut:
    player = repository.get_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    statistics = repository.get_career_statistics(player_id)
    years = [
        season.start_year
        for season in repository.list_seasons_for_player(player_id)
        if season.start_year
    ]
    return player_out_from_domain(player, statistics, max(years, default=None))


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
        season_out_from_domain(season, repository.get_season_team(player_id, season))
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


@router.get(
    "/{player_id}/seasons/{competition}/{label}/percentiles",
    response_model=PercentileReportOut,
)
def get_player_season_percentiles(
    player_id: int,
    competition: str,
    label: str,
    use_case: GetPlayerPercentilesUseCaseDep,
) -> PercentileReportOut:
    try:
        report = use_case.execute(player_id, Season(competition, label))
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return percentile_report_out_from_domain(report)


@router.get("/{player_id}/twins", response_model=TwinReportOut)
def find_twins(
    player_id: int,
    use_case: FindTwinsUseCaseDep,
    competition: str | None = None,
    label: str | None = None,
    max_value: Annotated[int | None, Query(ge=0)] = None,
    max_age: Annotated[int | None, Query(ge=14, le=50)] = None,
    league: str | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
) -> TwinReportOut:
    try:
        report = use_case.execute(
            player_id,
            season=_season_or_none(competition, label),
            filters=TwinFilters(
                max_value=max_value, max_age=max_age, competition=league, limit=limit
            ),
        )
    except PlayerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return twin_report_out_from_domain(report)


@router.get("/{player_id}/shots", response_model=list[PlayerShotOut])
def list_player_shots(
    player_id: int,
    repository: ShotRepositoryDep,
    season_label: str | None = None,
) -> list[PlayerShotOut]:
    shots = repository.list_player_shots(player_id, season_label)
    return [player_shot_out_from_domain(entry) for entry in shots]


@router.get("/{player_id}/market-value", response_model=MarketValueHistoryOut)
def get_market_value(
    player_id: int, repository: PlayerRepositoryDep
) -> MarketValueHistoryOut:
    player = repository.get_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=404, detail=f"No player found with id {player_id}"
        )
    history = repository.list_market_value_history(player_id)
    return market_value_history_out_from_domain(history)


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
