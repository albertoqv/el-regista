from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta

from player_scouting.application.player_matching import name_tokens
from player_scouting.application.ports import (
    Fixture,
    MatchStats,
    MatchStatsProvider,
    MatchStatsRepository,
    TeamRepository,
)
from player_scouting.application.use_cases.team_analytics import (
    _labels_up_to,
    _record,
)
from player_scouting.domain.counts import (
    CountRecord,
    StatPrediction,
    count_ratings,
    dispersion,
    stat_prediction,
)
from player_scouting.domain.market import implied_probabilities
from player_scouting.domain.prediction import (
    MatchPrediction,
    predict,
    score_matrix,
    team_ratings,
)

# Stat -> (home column, away column) in MatchStats, and the lines we price.
STATS: dict[str, tuple[str, str, tuple[float, ...]]] = {
    "corners": ("home_corners", "away_corners", (7.5, 8.5, 9.5, 10.5, 11.5)),
    "yellows": ("home_yellows", "away_yellows", (2.5, 3.5, 4.5, 5.5, 6.5)),
    "fouls": ("home_fouls", "away_fouls", (19.5, 21.5, 23.5, 25.5, 27.5)),
    "shots": ("home_shots", "away_shots", (20.5, 22.5, 24.5, 26.5, 28.5)),
    "shots_on_target": (
        "home_shots_on_target",
        "away_shots_on_target",
        (6.5, 7.5, 8.5, 9.5, 10.5),
    ),
}
GOAL_LINES = (0.5, 1.5, 2.5, 3.5, 4.5)
HEAD_TO_HEAD = 6
RECENT = 5
# A referee's own average counts as this many "league average" matches.
REFEREE_PRIOR_MATCHES = 10


def _played(matches: list[MatchStats]) -> list[MatchStats]:
    return [m for m in matches if m.played]


def learn_team_names(
    fixtures: list[Fixture], stats: list[MatchStats]
) -> dict[str, str]:
    """Understat name -> football-data name, learned from matches both sources
    report on the same day (±1) with the same score; majority vote per team."""
    by_day: dict[tuple[str, date], list[MatchStats]] = defaultdict(list)
    for match in _played(stats):
        by_day[(match.competition, match.played_on)].append(match)
    votes: dict[str, Counter[str]] = defaultdict(Counter)
    for fixture in fixtures:
        if not fixture.played:
            continue
        day = fixture.kickoff.date()
        candidates = [
            m
            for offset in (-1, 0, 1)
            for m in by_day.get((fixture.competition, day + timedelta(days=offset)), [])
            if (m.home_goals, m.away_goals) == (fixture.home_goals, fixture.away_goals)
        ]
        if len(candidates) > 1:
            # Several results alike that day: keep those that share a name word.
            candidates = [
                m
                for m in candidates
                if name_tokens(m.home_team) & name_tokens(fixture.home_team)
                or name_tokens(m.away_team) & name_tokens(fixture.away_team)
            ]
        if len(candidates) == 1:
            votes[fixture.home_team][candidates[0].home_team] += 1
            votes[fixture.away_team][candidates[0].away_team] += 1
    return {team: counter.most_common(1)[0][0] for team, counter in votes.items()}


@dataclass
class IngestMatchStatsUseCase:
    provider: MatchStatsProvider
    repository: MatchStatsRepository

    def execute(self, start_year: int) -> int:
        matches = self.provider.season(start_year) + self.provider.upcoming()
        self.repository.save_match_stats(matches)
        return len(matches)


@dataclass(frozen=True)
class RefereeProfile:
    name: str
    matches: int
    yellows_per_match: float
    multiplier: float


@dataclass(frozen=True)
class MatchInsights:
    fixture: Fixture
    result: MatchPrediction
    market: tuple[float, float, float] | None
    consensus: tuple[float, float, float]
    goals_over: dict[float, float]
    home_clean_sheet: float
    away_clean_sheet: float
    half_time: tuple[float, float, float]
    stats: dict[str, StatPrediction]
    referee: RefereeProfile | None
    head_to_head: list[MatchStats]
    home_recent: list[MatchStats]
    away_recent: list[MatchStats]
    home_name: str
    away_name: str


def _records(
    matches: list[MatchStats], home_column: str, away_column: str
) -> list[CountRecord]:
    records = []
    for m in matches:
        home_value = getattr(m, home_column)
        away_value = getattr(m, away_column)
        if home_value is None or away_value is None:
            continue
        records += [
            CountRecord(
                m.home_team, m.away_team, True, m.played_on, home_value, away_value
            ),
            CountRecord(
                m.away_team, m.home_team, False, m.played_on, away_value, home_value
            ),
        ]
    return records


def _involving(matches: list[MatchStats], team: str) -> list[MatchStats]:
    return [m for m in matches if team in (m.home_team, m.away_team)]


def _referee(name: str | None, matches: list[MatchStats]) -> RefereeProfile | None:
    if not name:
        return None
    totals = [
        m.home_yellows + m.away_yellows
        for m in matches
        if m.home_yellows is not None and m.away_yellows is not None
    ]
    own = [
        m.home_yellows + m.away_yellows
        for m in matches
        if m.referee == name
        and m.home_yellows is not None
        and m.away_yellows is not None
    ]
    if not totals:
        return None
    league = sum(totals) / len(totals)
    shrunk = (sum(own) + REFEREE_PRIOR_MATCHES * league) / (
        len(own) + REFEREE_PRIOR_MATCHES
    )
    return RefereeProfile(
        name=name,
        matches=len(own),
        yellows_per_match=sum(own) / len(own) if own else league,
        multiplier=shrunk / league if league else 1.0,
    )


@dataclass
class MatchInsightsUseCase:
    teams: TeamRepository
    stats: MatchStatsRepository
    today: Callable[[], date] = field(default=date.today)

    def execute(self, match_id: int) -> MatchInsights | None:
        fixture = next(
            (f for f in self.teams.list_fixtures() if f.match_id == match_id), None
        )
        if fixture is None:
            return None
        today = self.today()
        labels = _labels_up_to(fixture.season_label)
        history = self.teams.list_team_matches(labels, fixture.competition)
        result = predict(
            team_ratings([_record(m) for m in history], today),
            fixture.home_team,
            fixture.away_team,
        )
        league_stats = self.stats.list_match_stats(fixture.competition, labels)
        names = learn_team_names(
            [
                f
                for f in self.teams.list_fixtures(fixture.competition)
                if f.season_label in labels
            ],
            league_stats,
        )
        home_name = names.get(fixture.home_team, fixture.home_team)
        away_name = names.get(fixture.away_team, fixture.away_team)
        played = [
            m for m in _played(league_stats) if m.played_on < fixture.kickoff.date()
        ]
        upcoming = self.stats.find_upcoming(
            fixture.competition, fixture.kickoff.date(), home_name, away_name
        )

        market = None
        if (
            upcoming
            and upcoming.odds_home
            and upcoming.odds_draw
            and upcoming.odds_away
        ):
            market = implied_probabilities(
                upcoming.odds_home, upcoming.odds_draw, upcoming.odds_away
            )
        model = (result.home_win, result.draw, result.away_win)
        consensus = (
            tuple((a + b) / 2 for a, b in zip(model, market, strict=True))
            if market
            else model
        )

        matrix = score_matrix(result.expected_home, result.expected_away)
        cells = [(h, a, p) for h, row in enumerate(matrix) for a, p in enumerate(row)]
        referee = _referee(upcoming.referee if upcoming else None, played)

        stats = {}
        for stat, (home_column, away_column, lines) in STATS.items():
            records = _records(played, home_column, away_column)
            if not records:
                continue
            multiplier = referee.multiplier if (stat == "yellows" and referee) else 1.0
            stats[stat] = stat_prediction(
                count_ratings(records, today),
                home_name,
                away_name,
                dispersion=dispersion([r.value_for for r in records]),
                lines=lines,
                multiplier=multiplier,
            )

        half_time = self._half_time(played, home_name, away_name, today)
        meetings = [
            m
            for m in reversed(played)
            if {m.home_team, m.away_team} == {home_name, away_name}
        ]
        return MatchInsights(
            fixture=fixture,
            result=result,
            market=market,  # type: ignore[arg-type]
            consensus=consensus,  # type: ignore[arg-type]
            goals_over={
                line: sum(p for h, a, p in cells if h + a > line) for line in GOAL_LINES
            },
            home_clean_sheet=sum(p for h, a, p in cells if a == 0),
            away_clean_sheet=sum(p for h, a, p in cells if h == 0),
            half_time=half_time,
            stats=stats,
            referee=referee,
            head_to_head=meetings[:HEAD_TO_HEAD],
            home_recent=list(reversed(_involving(played, home_name)))[:RECENT],
            away_recent=list(reversed(_involving(played, away_name)))[:RECENT],
            home_name=home_name,
            away_name=away_name,
        )

    @staticmethod
    def _half_time(
        played: list[MatchStats], home: str, away: str, today: date
    ) -> tuple[float, float, float]:
        records = _records(played, "home_goals_ht", "away_goals_ht")
        if not records:
            return (1 / 3, 1 / 3, 1 / 3)
        ratings = count_ratings(records, today)
        rate_home = (
            ratings.home_average
            * ratings.for_.get(home, 1.0)
            * ratings.against.get(away, 1.0)
        )
        rate_away = (
            ratings.away_average
            * ratings.for_.get(away, 1.0)
            * ratings.against.get(home, 1.0)
        )
        matrix = score_matrix(rate_home, rate_away, rho=0.0)
        cells = [(h, a, p) for h, row in enumerate(matrix) for a, p in enumerate(row)]
        return (
            sum(p for h, a, p in cells if h > a),
            sum(p for h, a, p in cells if h == a),
            sum(p for h, a, p in cells if h < a),
        )


@dataclass(frozen=True)
class StatBacktest:
    matches: int
    model_mae: float
    baseline_mae: float
    line: float
    model_brier: float
    baseline_brier: float


@dataclass
class StatsBacktestUseCase:
    """Walk-forward test of each stat model against the league average."""

    repository: MatchStatsRepository
    minimum_history: int = 40

    def execute(self, competition: str, season_label: str) -> dict[str, StatBacktest]:
        matches = _played(
            self.repository.list_match_stats(competition, _labels_up_to(season_label))
        )
        report = {}
        for stat, (home_column, away_column, lines) in STATS.items():
            line = lines[len(lines) // 2]
            errors_model, errors_base, brier_model, brier_base = [], [], [], []
            for index, match in enumerate(matches):
                if match.season_label != season_label or index < self.minimum_history:
                    continue
                actual_home = getattr(match, home_column)
                actual_away = getattr(match, away_column)
                if actual_home is None or actual_away is None:
                    continue
                earlier = [m for m in matches[:index] if m.played_on < match.played_on]
                records = _records(earlier, home_column, away_column)
                if len(records) < 2 * self.minimum_history:
                    continue
                prediction = stat_prediction(
                    count_ratings(records, match.played_on),
                    match.home_team,
                    match.away_team,
                    dispersion=dispersion([r.value_for for r in records]),
                    lines=(line,),
                )
                actual = actual_home + actual_away
                league_total = 2 * sum(r.value_for for r in records) / len(records)
                over = 1.0 if actual > line else 0.0
                base_over = sum(
                    1
                    for m in earlier
                    if getattr(m, home_column) is not None
                    and getattr(m, home_column) + getattr(m, away_column) > line
                ) / max(len(records) // 2, 1)
                errors_model.append(abs(prediction.expected_total - actual))
                errors_base.append(abs(league_total - actual))
                brier_model.append((prediction.over[line] - over) ** 2)
                brier_base.append((base_over - over) ** 2)
            count = len(errors_model)
            if count:
                report[stat] = StatBacktest(
                    matches=count,
                    model_mae=sum(errors_model) / count,
                    baseline_mae=sum(errors_base) / count,
                    line=line,
                    model_brier=sum(brier_model) / count,
                    baseline_brier=sum(brier_base) / count,
                )
        return report
