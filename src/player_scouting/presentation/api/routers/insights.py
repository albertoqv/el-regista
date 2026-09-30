from __future__ import annotations

import time
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from player_scouting.application.ports import MatchStats
from player_scouting.application.use_cases.match_insights import (
    Highlights,
    HighlightsUseCase,
    MarketBenchmark,
    MarketBenchmarkUseCase,
    MatchInsightsUseCase,
    StatBacktest,
    StatsBacktestUseCase,
)
from player_scouting.application.use_cases.player_markets import (
    PlayerMarketLine,
    PlayerMarketsBacktest,
    PlayerMarketsBacktestUseCase,
    PlayerMarketsUseCase,
)
from player_scouting.domain.counts import StatPrediction
from player_scouting.presentation.api.dependencies import (
    MatchStatsRepositoryDep,
    PlayerRepositoryDep,
    ShotRepositoryDep,
    TeamRepositoryDep,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])

BACKTEST_CACHE_SECONDS = 3600
_cache: dict[tuple, tuple[float, dict[str, StatBacktest]]] = {}
_players_cache: dict[tuple, tuple[float, PlayerMarketsBacktest]] = {}
_benchmark_cache: dict[tuple, tuple[float, MarketBenchmark]] = {}
HIGHLIGHTS_CACHE_SECONDS = 600
_highlights_cache: dict[int, tuple[float, Highlights]] = {}


class PickOut(BaseModel):
    match_id: int
    competition: str
    kickoff: str
    home_team: str
    away_team: str
    category: str
    label: str
    probability: float


class HighlightsOut(BaseModel):
    window_start: str
    window_end: str
    picks: list[PickOut]


class PlayerMarketOut(BaseModel):
    understat_player_id: int
    player_id: int | None
    name: str
    photo_url: str | None
    position: str
    plays: float
    expected_minutes: float
    goal: float
    assist: float
    card: float
    shots_1: float
    shots_2: float


class PlayerMarketsOut(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    home: list[PlayerMarketOut]
    away: list[PlayerMarketOut]


class PlayerMarketsBacktestOut(BaseModel):
    predictions: int
    brier: float
    baseline_brier: float
    calibration: list[dict[str, float]]


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


@router.get("/market-benchmark")
def market_benchmark(
    teams: TeamRepositoryDep,
    stats: MatchStatsRepositoryDep,
    season: str,
    minimum_history: Annotated[int, Query(ge=0)] = 30,
) -> dict[str, float]:
    key = (season, minimum_history)
    cached = _benchmark_cache.get(key)
    if cached is None or time.monotonic() - cached[0] > BACKTEST_CACHE_SECONDS:
        report = MarketBenchmarkUseCase(teams, stats, minimum_history).execute(season)
        cached = (time.monotonic(), report)
        _benchmark_cache[key] = cached
    report = cached[1]
    return {
        "matches": report.matches,
        "model_brier": round(report.model_brier, 4),
        "market_brier": round(report.market_brier, 4),
        "consensus_brier": round(report.consensus_brier, 4),
        "model_accuracy": round(report.model_accuracy, 4),
        "market_accuracy": round(report.market_accuracy, 4),
    }


@router.get("/highlights", response_model=HighlightsOut)
def highlights(
    teams: TeamRepositoryDep,
    stats: MatchStatsRepositoryDep,
    shots: ShotRepositoryDep,
    per_category: Annotated[int, Query(ge=1, le=20)] = 5,
) -> HighlightsOut:
    cached = _highlights_cache.get(per_category)
    if cached is None or time.monotonic() - cached[0] > HIGHLIGHTS_CACHE_SECONDS:
        cached = (
            time.monotonic(),
            HighlightsUseCase(teams, stats, shots).execute(per_category),
        )
        _highlights_cache[per_category] = cached
    report = cached[1]
    return HighlightsOut(
        window_start=report.window_start.isoformat(),
        window_end=report.window_end.isoformat(),
        picks=[
            PickOut(
                match_id=pick.fixture.match_id,
                competition=pick.fixture.competition,
                kickoff=pick.fixture.kickoff.isoformat(),
                home_team=pick.fixture.home_team,
                away_team=pick.fixture.away_team,
                category=pick.category,
                label=pick.label,
                probability=round(pick.probability, 4),
            )
            for pick in report.picks
        ],
    )


@router.get("/players-backtest", response_model=PlayerMarketsBacktestOut)
def players_backtest(
    shots: ShotRepositoryDep,
    competition: str,
    season: str,
    minimum_matches: Annotated[int, Query(ge=0)] = 30,
) -> PlayerMarketsBacktestOut:
    key = (competition, season, minimum_matches)
    cached = _players_cache.get(key)
    if cached is None or time.monotonic() - cached[0] > BACKTEST_CACHE_SECONDS:
        report = PlayerMarketsBacktestUseCase(shots, minimum_matches).execute(
            competition, season
        )
        cached = (time.monotonic(), report)
        _players_cache[key] = cached
    report = cached[1]
    return PlayerMarketsBacktestOut(
        predictions=report.predictions,
        brier=round(report.brier, 4),
        baseline_brier=round(report.baseline_brier, 4),
        calibration=[
            {"predicted": round(p, 4), "observed": round(o, 4), "count": n}
            for p, o, n in report.calibration
        ],
    )


@router.get("/{match_id}/players", response_model=PlayerMarketsOut)
def player_markets(
    match_id: int,
    teams: TeamRepositoryDep,
    shots: ShotRepositoryDep,
    players: PlayerRepositoryDep,
) -> PlayerMarketsOut:
    markets = PlayerMarketsUseCase(teams, shots).execute(match_id)
    if markets is None:
        raise HTTPException(status_code=404, detail=f"No fixture {match_id}")
    known = players.find_by_understat_ids(
        [line.understat_player_id for line in markets.home + markets.away]
    )

    def out(line: PlayerMarketLine) -> PlayerMarketOut:
        player = known.get(line.understat_player_id)
        props = line.props
        return PlayerMarketOut(
            understat_player_id=line.understat_player_id,
            player_id=player.player_id if player else None,
            name=player.name if player else line.name,
            photo_url=player.photo_url if player else None,
            position=line.position,
            plays=round(line.plays, 4),
            expected_minutes=round(props.expected_minutes, 1),
            goal=round(props.goal, 4),
            assist=round(props.assist, 4),
            card=round(props.card, 4),
            shots_1=round(props.shots_1, 4),
            shots_2=round(props.shots_2, 4),
        )

    return PlayerMarketsOut(
        match_id=markets.fixture.match_id,
        home_team=markets.fixture.home_team,
        away_team=markets.fixture.away_team,
        home=[out(line) for line in markets.home],
        away=[out(line) for line in markets.away],
    )


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
