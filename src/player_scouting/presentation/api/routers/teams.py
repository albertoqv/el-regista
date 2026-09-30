from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Query

from player_scouting.application.use_cases.team_analytics import (
    BacktestReport,
    BacktestUseCase,
    LeagueTableUseCase,
    PredictFixturesUseCase,
)
from player_scouting.presentation.api.dependencies import (
    ShotRepositoryDep,
    TeamRepositoryDep,
)
from player_scouting.presentation.api.schemas import (
    BacktestReportOut,
    FixtureForecastOut,
    ShotLeaderOut,
    TableRowOut,
    TeamMatchOut,
    backtest_report_out_from_domain,
    fixture_forecast_out_from_domain,
    shot_leader_out_from_domain,
    table_row_out_from_domain,
    team_match_out_from_domain,
)

teams_router = APIRouter(prefix="/teams", tags=["teams"])
predictions_router = APIRouter(prefix="/predictions", tags=["predictions"])

# Walk-forward backtests replay a whole season: keep the result for an hour.
BACKTEST_CACHE_SECONDS = 3600
_backtest_cache: dict[tuple, tuple[float, BacktestReport]] = {}


@teams_router.get("/table", response_model=list[TableRowOut])
def league_table(
    repository: TeamRepositoryDep, season: str, competition: str
) -> list[TableRowOut]:
    rows = LeagueTableUseCase(repository).execute(season, competition)
    return [
        table_row_out_from_domain(row, position) for position, row in enumerate(rows, 1)
    ]


@teams_router.get("/matches", response_model=list[TeamMatchOut])
def team_matches(
    repository: TeamRepositoryDep, team: str, season: str
) -> list[TeamMatchOut]:
    matches = repository.list_team_matches([season])
    return [team_match_out_from_domain(m) for m in matches if m.team == team]


@teams_router.get("/players", response_model=list[ShotLeaderOut])
def team_players(
    repository: ShotRepositoryDep,
    team: str,
    season: str,
    limit: Annotated[int, Query(ge=1, le=40)] = 12,
) -> list[ShotLeaderOut]:
    players = repository.list_team_players(season, team)[:limit]
    return [shot_leader_out_from_domain(player) for player in players]


@predictions_router.get("", response_model=list[FixtureForecastOut])
def predictions(
    repository: TeamRepositoryDep,
    days: Annotated[int, Query(ge=1, le=4000)] = 10,
    competition: str | None = None,
) -> list[FixtureForecastOut]:
    forecasts = PredictFixturesUseCase(repository).execute(days, competition)
    return [fixture_forecast_out_from_domain(f) for f in forecasts]


@predictions_router.get("/backtest", response_model=BacktestReportOut)
def backtest(
    repository: TeamRepositoryDep,
    season: str,
    competition: str | None = None,
    minimum_history: Annotated[int, Query(ge=0)] = 30,
) -> BacktestReportOut:
    key = (season, competition, minimum_history)
    cached = _backtest_cache.get(key)
    if cached is None or time.monotonic() - cached[0] > BACKTEST_CACHE_SECONDS:
        report = BacktestUseCase(repository, minimum_history).execute(
            [season], competition
        )
        cached = (time.monotonic(), report)
        _backtest_cache[key] = cached
    return backtest_report_out_from_domain(cached[1])
