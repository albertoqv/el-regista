from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from player_scouting.application.ports import (
    Fixture,
    MatchStatsRepository,
    PredictionLogRepository,
    PredictionSnapshot,
    TeamRepository,
)
from player_scouting.application.use_cases.match_insights import MatchInsightsUseCase
from player_scouting.application.use_cases.team_analytics import (
    BacktestUseCase,
    ScoredMatch,
)

# A pick counts as "confident" when its most likely outcome is at least this likely.
CONFIDENT = 0.6
RECENT_PICKS = 30

Probabilities = tuple[float, float, float]


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _outcome(fixture: Fixture) -> int:
    assert fixture.home_goals is not None and fixture.away_goals is not None
    if fixture.home_goals > fixture.away_goals:
        return 0
    return 1 if fixture.home_goals == fixture.away_goals else 2


def _pick(probabilities: Probabilities) -> int:
    return max(range(3), key=lambda i: probabilities[i])


def _brier(probabilities: Probabilities, outcome: int) -> float:
    return sum(
        (p - (1.0 if i == outcome else 0.0)) ** 2 for i, p in enumerate(probabilities)
    )


@dataclass
class SnapshotPredictionsUseCase:
    """Stores what the site shows for the coming days, before kickoff.

    Only fixtures that have not started are written, so a forecast can be
    refreshed until kickoff but never edited once the match is under way.
    """

    teams: TeamRepository
    stats: MatchStatsRepository
    log: PredictionLogRepository
    now: Callable[[], datetime] = field(default=datetime.now)

    def execute(self, days: int = 7) -> int:
        start = self.now()
        upcoming = [
            f
            for f in self.teams.list_fixtures(
                start=start, end=start + timedelta(days=days)
            )
            if not f.played
        ]
        insights = MatchInsightsUseCase(self.teams, self.stats, lambda: start.date())
        for fixture in upcoming:
            forecast = insights.for_fixture(fixture)
            self.log.save_snapshot(
                PredictionSnapshot(
                    match_id=fixture.match_id,
                    competition=fixture.competition,
                    season_label=fixture.season_label,
                    kickoff=fixture.kickoff,
                    home_team=fixture.home_team,
                    away_team=fixture.away_team,
                    made_at=start,
                    model=(
                        forecast.result.home_win,
                        forecast.result.draw,
                        forecast.result.away_win,
                    ),
                    market=forecast.market,
                    over_2_5=forecast.goals_over[2.5],
                )
            )
        return len(upcoming)


@dataclass(frozen=True)
class RecordTotals:
    matches: int
    hits: int
    brier: float
    confident: int
    confident_hits: int
    market_matches: int
    market_hits: int
    market_brier: float | None


@dataclass(frozen=True)
class WeekRecord(RecordTotals):
    week_start: date


@dataclass(frozen=True)
class ScoredPick:
    match_id: int
    competition: str
    kickoff: datetime
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    model: Probabilities
    market: Probabilities | None
    model_hit: bool
    market_hit: bool | None
    over_2_5: float | None
    over_hit: bool | None


@dataclass(frozen=True)
class TrackRecord:
    season_label: str
    live_total: RecordTotals
    live_weeks: list[WeekRecord]
    live_recent: list[ScoredPick]
    pending: int
    rebuilt_total: RecordTotals
    rebuilt_weeks: list[WeekRecord]


def _totals(picks: list[ScoredPick]) -> RecordTotals:
    count = len(picks)
    confident = [p for p in picks if max(p.model) >= CONFIDENT]
    with_market = [p for p in picks if p.market is not None]
    return RecordTotals(
        matches=count,
        hits=sum(p.model_hit for p in picks),
        brier=(
            sum(_brier(p.model, _outcome_of(p)) for p in picks) / count
            if count
            else 0.0
        ),
        confident=len(confident),
        confident_hits=sum(p.model_hit for p in confident),
        market_matches=len(with_market),
        market_hits=sum(bool(p.market_hit) for p in with_market),
        market_brier=(
            sum(
                _brier(p.market, _outcome_of(p))
                for p in with_market
                if p.market is not None
            )
            / len(with_market)
            if with_market
            else None
        ),
    )


def _outcome_of(pick: ScoredPick) -> int:
    if pick.home_goals > pick.away_goals:
        return 0
    return 1 if pick.home_goals == pick.away_goals else 2


def _weeks(picks: list[ScoredPick]) -> list[WeekRecord]:
    by_week: dict[date, list[ScoredPick]] = defaultdict(list)
    for pick in picks:
        by_week[week_start(pick.kickoff.date())].append(pick)
    return [
        WeekRecord(week_start=week, **vars(_totals(items)))
        for week, items in sorted(by_week.items())
    ]


def _scored(
    fixture: Fixture,
    model: Probabilities,
    market: Probabilities | None,
    over_2_5: float | None,
) -> ScoredPick:
    assert fixture.home_goals is not None and fixture.away_goals is not None
    outcome = _outcome(fixture)
    goals = fixture.home_goals + fixture.away_goals
    return ScoredPick(
        match_id=fixture.match_id,
        competition=fixture.competition,
        kickoff=fixture.kickoff,
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        home_goals=fixture.home_goals,
        away_goals=fixture.away_goals,
        model=model,
        market=market,
        model_hit=_pick(model) == outcome,
        market_hit=_pick(market) == outcome if market else None,
        over_2_5=over_2_5,
        over_hit=((over_2_5 >= 0.5) == (goals > 2)) if over_2_5 is not None else None,
    )


@dataclass
class TrackRecordUseCase:
    teams: TeamRepository
    log: PredictionLogRepository
    minimum_history: int = 30

    def execute(self, season_label: str) -> TrackRecord:
        fixtures = {f.match_id: f for f in self.teams.list_fixtures()}
        live: list[ScoredPick] = []
        pending = 0
        for snapshot in self.log.list_snapshots():
            fixture = fixtures.get(snapshot.match_id)
            if fixture is None or not fixture.played:
                pending += 1
                continue
            live.append(
                _scored(fixture, snapshot.model, snapshot.market, snapshot.over_2_5)
            )
        rebuilt = [
            self._rebuilt(match)
            for match in BacktestUseCase(
                self.teams, self.minimum_history
            ).scored_matches([season_label])
        ]
        live.sort(key=lambda p: (p.kickoff, p.match_id))
        return TrackRecord(
            season_label=season_label,
            live_total=_totals(live),
            live_weeks=_weeks(live),
            live_recent=live[::-1][:RECENT_PICKS],
            pending=pending,
            rebuilt_total=_totals(rebuilt),
            rebuilt_weeks=_weeks(rebuilt),
        )

    @staticmethod
    def _rebuilt(match: ScoredMatch) -> ScoredPick:
        return _scored(match.fixture, match.model, None, None)
