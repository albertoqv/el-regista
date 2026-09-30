from __future__ import annotations

import time
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from player_scouting.application.ports import MatchStats
from player_scouting.application.use_cases.match_insights import (
    MatchInsightsUseCase,
    StatBacktest,
    StatsBacktestUseCase,
)
from player_scouting.domain.counts import StatPrediction
from player_scouting.presentation.api.dependencies import (
    MatchStatsRepositoryDep,
    TeamRepositoryDep,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])

BACKTEST_CACHE_SECONDS = 3600
_cache: dict[tuple, tuple[float, dict[str, StatBacktest]]] = {}


class OutcomeOut(BaseModel):
    home_win: float
    draw: float
    away_win: float


class LineOut(BaseModel):
    line: float
    over: float


class StatOut(BaseModel):
    stat: str
    expected_home: float
    expected_away: float
    expected_total: float
    home_more: float
    equal: float
    away_more: float
    over: list[LineOut]
    distribution: list[float]


class RefereeOut(BaseModel):
    name: str
    matches: int
    yellows_per_match: float
    multiplier: float


class MatchLineOut(BaseModel):
    played_on: date
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    home_corners: int | None
    away_corners: int | None
    home_yellows: int | None
    away_yellows: int | None
    home_shots: int | None
    away_shots: int | None


class InsightsOut(BaseModel):
    match_id: int
    competition: str
    kickoff: str
    home_team: str
    away_team: str
    expected_home: float
    expected_away: float
    result: OutcomeOut
    market: OutcomeOut | None
    consensus: OutcomeOut
    scorelines: list[dict[str, float]]
    goals_over: list[LineOut]
    both_teams_score: float
    home_clean_sheet: float
    away_clean_sheet: float
    half_time: OutcomeOut
    stats: list[StatOut]
    referee: RefereeOut | None
    head_to_head: list[MatchLineOut]
    home_recent: list[MatchLineOut]
    away_recent: list[MatchLineOut]


class StatBacktestOut(BaseModel):
    stat: str
    matches: int
    model_mae: float
    baseline_mae: float
    line: float
    model_brier: float
    baseline_brier: float


def _outcome(values: tuple[float, float, float]) -> OutcomeOut:
    home, draw, away = values
    return OutcomeOut(
        home_win=round(home, 4), draw=round(draw, 4), away_win=round(away, 4)
    )


def _stat(name: str, prediction: StatPrediction) -> StatOut:
    distribution = list(prediction.total_distribution)
    # Trim the long empty tail for the chart.
    while len(distribution) > 1 and distribution[-1] < 1e-4:
        distribution.pop()
    return StatOut(
        stat=name,
        expected_home=round(prediction.expected_home, 2),
        expected_away=round(prediction.expected_away, 2),
        expected_total=round(prediction.expected_total, 2),
        home_more=round(prediction.home_more, 4),
        equal=round(prediction.equal, 4),
        away_more=round(prediction.away_more, 4),
        over=[
            LineOut(line=line, over=round(p, 4)) for line, p in prediction.over.items()
        ],
        distribution=[round(p, 4) for p in distribution],
    )


def _line(match: MatchStats) -> MatchLineOut:
    return MatchLineOut(
        **{name: getattr(match, name) for name in MatchLineOut.model_fields}
    )


@router.get("/stats-backtest", response_model=list[StatBacktestOut])
def stats_backtest(
    repository: MatchStatsRepositoryDep,
    competition: str,
    season: str,
    minimum_history: Annotated[int, Query(ge=0)] = 40,
) -> list[StatBacktestOut]:
    key = (competition, season, minimum_history)
    cached = _cache.get(key)
    if cached is None or time.monotonic() - cached[0] > BACKTEST_CACHE_SECONDS:
        report = StatsBacktestUseCase(repository, minimum_history).execute(
            competition, season
        )
        cached = (time.monotonic(), report)
        _cache[key] = cached
    return [
        StatBacktestOut(
            stat=stat,
            matches=result.matches,
            model_mae=round(result.model_mae, 3),
            baseline_mae=round(result.baseline_mae, 3),
            line=result.line,
            model_brier=round(result.model_brier, 4),
            baseline_brier=round(result.baseline_brier, 4),
        )
        for stat, result in cached[1].items()
    ]


@router.get("/{match_id}/insights", response_model=InsightsOut)
def match_insights(
    match_id: int, teams: TeamRepositoryDep, stats: MatchStatsRepositoryDep
) -> InsightsOut:
    insights = MatchInsightsUseCase(teams, stats).execute(match_id)
    if insights is None:
        raise HTTPException(status_code=404, detail=f"No fixture {match_id}")
    fixture, result = insights.fixture, insights.result
    return InsightsOut(
        match_id=fixture.match_id,
        competition=fixture.competition,
        kickoff=fixture.kickoff.isoformat(),
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        expected_home=round(result.expected_home, 2),
        expected_away=round(result.expected_away, 2),
        result=_outcome((result.home_win, result.draw, result.away_win)),
        market=_outcome(insights.market) if insights.market else None,
        consensus=_outcome(insights.consensus),
        scorelines=[
            {"home": h, "away": a, "probability": round(p, 4)}
            for h, a, p in result.scorelines
        ],
        goals_over=[
            LineOut(line=line, over=round(p, 4))
            for line, p in insights.goals_over.items()
        ],
        both_teams_score=round(result.both_teams_score, 4),
        home_clean_sheet=round(insights.home_clean_sheet, 4),
        away_clean_sheet=round(insights.away_clean_sheet, 4),
        half_time=_outcome(insights.half_time),
        stats=[_stat(name, prediction) for name, prediction in insights.stats.items()],
        referee=RefereeOut(
            name=insights.referee.name,
            matches=insights.referee.matches,
            yellows_per_match=round(insights.referee.yellows_per_match, 2),
            multiplier=round(insights.referee.multiplier, 3),
        )
        if insights.referee
        else None,
        head_to_head=[_line(m) for m in insights.head_to_head],
        home_recent=[_line(m) for m in insights.home_recent],
        away_recent=[_line(m) for m in insights.away_recent],
    )
