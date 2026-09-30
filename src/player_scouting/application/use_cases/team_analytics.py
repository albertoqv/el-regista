from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from player_scouting.application.ports import (
    Fixture,
    TeamDataProvider,
    TeamMatch,
    TeamRepository,
)
from player_scouting.domain.prediction import (
    LeagueRatings,
    MatchPrediction,
    TeamMatchRecord,
    predict,
    team_ratings,
)

FORM_MATCHES = 5
# A season's forecasts also learn from the previous season (time-decayed).
HISTORY_SEASONS = 2


def _record(match: TeamMatch) -> TeamMatchRecord:
    return TeamMatchRecord(
        team=match.team,
        opponent=match.opponent,
        home=match.home,
        played_on=match.played_on,
        goals_for=match.goals_for,
        goals_against=match.goals_against,
        xg_for=match.xg_for,
        xg_against=match.xg_against,
    )


def _labels_up_to(season_label: str) -> list[str]:
    year = int(season_label)
    return [str(year - offset) for offset in range(HISTORY_SEASONS)]


def _form(matches: list[TeamMatch], team: str) -> list[str]:
    """Latest results first: w / d / l."""
    own = [m for m in matches if m.team == team]
    return [m.result for m in reversed(own)][:FORM_MATCHES]


@dataclass(frozen=True)
class TeamSeasonSummary:
    fixtures: int
    team_matches: int


@dataclass
class IngestTeamSeasonUseCase:
    provider: TeamDataProvider
    repository: TeamRepository

    def execute(self, start_year: int) -> TeamSeasonSummary:
        fixtures, matches = self.provider.get_team_season(start_year)
        self.repository.save_team_season(fixtures, matches)
        return TeamSeasonSummary(fixtures=len(fixtures), team_matches=len(matches))


@dataclass(frozen=True)
class TableRow:
    team: str
    competition: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    xg_for: float
    xg_against: float
    npxg_difference: float
    xpts: float
    ppda: float | None
    ppda_allowed: float | None
    deep: int
    deep_allowed: int
    form: list[str]


@dataclass
class LeagueTableUseCase:
    repository: TeamRepository

    def execute(self, season_label: str, competition: str) -> list[TableRow]:
        matches = self.repository.list_team_matches([season_label], competition)
        by_team: dict[str, list[TeamMatch]] = defaultdict(list)
        for match in matches:
            by_team[match.team].append(match)
        rows = [
            self._row(team, own, matches, competition) for team, own in by_team.items()
        ]
        rows.sort(
            key=lambda r: (
                -r.points,
                -(r.goals_for - r.goals_against),
                -r.goals_for,
                r.team,
            )
        )
        return rows

    @staticmethod
    def _row(
        team: str, own: list[TeamMatch], matches: list[TeamMatch], competition: str
    ) -> TableRow:
        wins = sum(m.result == "w" for m in own)
        draws = sum(m.result == "d" for m in own)
        ppdas = [m.ppda for m in own if m.ppda is not None]
        allowed = [m.ppda_allowed for m in own if m.ppda_allowed is not None]
        return TableRow(
            team=team,
            competition=competition,
            played=len(own),
            wins=wins,
            draws=draws,
            losses=len(own) - wins - draws,
            goals_for=sum(m.goals_for for m in own),
            goals_against=sum(m.goals_against for m in own),
            points=3 * wins + draws,
            xg_for=sum(m.xg_for for m in own),
            xg_against=sum(m.xg_against for m in own),
            npxg_difference=sum(m.npxg_for - m.npxg_against for m in own),
            xpts=sum(m.xpts for m in own),
            ppda=sum(ppdas) / len(ppdas) if ppdas else None,
            ppda_allowed=sum(allowed) / len(allowed) if allowed else None,
            deep=sum(m.deep for m in own),
            deep_allowed=sum(m.deep_allowed for m in own),
            form=_form(matches, team),
        )


@dataclass(frozen=True)
class FixtureForecast:
    fixture: Fixture
    prediction: MatchPrediction
    home_form: list[str]
    away_form: list[str]


@dataclass
class PredictFixturesUseCase:
    repository: TeamRepository
    now: Callable[[], datetime] = field(default=datetime.now)

    def execute(
        self, days: int = 10, competition: str | None = None
    ) -> list[FixtureForecast]:
        start = self.now()
        upcoming = [
            f
            for f in self.repository.list_fixtures(
                competition, start=start, end=start + timedelta(days=days)
            )
            if not f.played
        ]
        forecasts = []
        cache: dict[tuple[str, str], tuple[LeagueRatings, list[TeamMatch]]] = {}
        for fixture in upcoming:
            key = (fixture.competition, fixture.season_label)
            if key not in cache:
                history = self.repository.list_team_matches(
                    _labels_up_to(fixture.season_label), fixture.competition
                )
                ratings = team_ratings([_record(m) for m in history], start.date())
                cache[key] = (ratings, history)
            ratings, history = cache[key]
            forecasts.append(
                FixtureForecast(
                    fixture=fixture,
                    prediction=predict(ratings, fixture.home_team, fixture.away_team),
                    home_form=_form(history, fixture.home_team),
                    away_form=_form(history, fixture.away_team),
                )
            )
        return forecasts


@dataclass(frozen=True)
class CalibrationBucket:
    predicted: float
    observed: float
    count: int


@dataclass(frozen=True)
class BacktestReport:
    matches: int
    accuracy: float
    brier: float
    log_loss: float
    baseline_accuracy: float
    baseline_brier: float
    calibration: list[CalibrationBucket]


def _outcome(fixture: Fixture) -> int:
    assert fixture.home_goals is not None and fixture.away_goals is not None
    if fixture.home_goals > fixture.away_goals:
        return 0
    return 1 if fixture.home_goals == fixture.away_goals else 2


def _brier(probabilities: tuple[float, float, float], outcome: int) -> float:
    return sum(
        (p - (1.0 if i == outcome else 0.0)) ** 2 for i, p in enumerate(probabilities)
    )


@dataclass
class BacktestUseCase:
    """Walk-forward test: each match is forecast only with data from before it."""

    repository: TeamRepository
    minimum_history: int = 30

    def execute(
        self, season_labels: list[str], competition: str | None = None
    ) -> BacktestReport:
        newest = max(season_labels, key=int)
        labels = sorted(
            set(season_labels) | set(_labels_up_to(min(season_labels, key=int)))
        )
        history = self.repository.list_team_matches(labels + [newest], competition)
        played = [
            f
            for f in self.repository.list_fixtures(competition)
            if f.played and f.season_label in season_labels
        ]
        scored: list[
            tuple[tuple[float, float, float], tuple[float, float, float], int]
        ] = []
        by_league: dict[str, list[Fixture]] = defaultdict(list)
        for fixture in played:
            by_league[fixture.competition].append(fixture)
        for league, fixtures in by_league.items():
            league_history = [m for m in history if m.competition == league]
            ratings_by_day: dict[date, LeagueRatings] = {}
            for fixture in fixtures:
                day = fixture.kickoff.date()
                earlier = [m for m in league_history if m.played_on < day]
                earlier_fixtures = len({m.match_id for m in earlier})
                if earlier_fixtures < self.minimum_history:
                    continue
                if day not in ratings_by_day:
                    ratings_by_day[day] = team_ratings(
                        [_record(m) for m in earlier], day
                    )
                prediction = predict(
                    ratings_by_day[day],
                    fixture.home_team,
                    fixture.away_team,
                )
                home = [m for m in earlier if m.home]
                total = len(home) or 1
                baseline = (
                    sum(m.result == "w" for m in home) / total,
                    sum(m.result == "d" for m in home) / total,
                    sum(m.result == "l" for m in home) / total,
                )
                model = (prediction.home_win, prediction.draw, prediction.away_win)
                scored.append((model, baseline, _outcome(fixture)))
        return self._report(scored)

    @staticmethod
    def _report(
        scored: list[
            tuple[tuple[float, float, float], tuple[float, float, float], int]
        ],
    ) -> BacktestReport:
        if not scored:
            return BacktestReport(0, 0.0, 0.0, 0.0, 0.0, 0.0, [])
        count = len(scored)
        buckets: dict[int, list[tuple[float, bool]]] = defaultdict(list)
        for model, _, outcome in scored:
            for index, probability in enumerate(model):
                buckets[min(int(probability * 10), 9)].append(
                    (probability, index == outcome)
                )
        return BacktestReport(
            matches=count,
            accuracy=sum(max(range(3), key=lambda i: m[i]) == o for m, _, o in scored)
            / count,
            brier=sum(_brier(m, o) for m, _, o in scored) / count,
            log_loss=-sum(math.log(max(m[o], 1e-9)) for m, _, o in scored) / count,
            baseline_accuracy=sum(
                max(range(3), key=lambda i: b[i]) == o for _, b, o in scored
            )
            / count,
            baseline_brier=sum(_brier(b, o) for _, b, o in scored) / count,
            calibration=[
                CalibrationBucket(
                    predicted=sum(p for p, _ in items) / len(items),
                    observed=sum(hit for _, hit in items) / len(items),
                    count=len(items),
                )
                for _, items in sorted(buckets.items())
            ],
        )
