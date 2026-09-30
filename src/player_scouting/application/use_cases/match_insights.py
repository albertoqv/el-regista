from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from player_scouting.application.player_matching import name_tokens
from player_scouting.application.ports import (
    Fixture,
    MatchStats,
    MatchStatsProvider,
    MatchStatsRepository,
    RosterEntry,
    ShotRepository,
    TeamRepository,
)
from player_scouting.application.use_cases.team_analytics import (
    _labels_up_to,
    _record,
)
from player_scouting.domain.counts import (
    CountRatings,
    CountRecord,
    StatPrediction,
    count_ratings,
    dispersion,
    stat_prediction,
)
from player_scouting.domain.market import implied_probabilities
from player_scouting.domain.prediction import (
    LeagueRatings,
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
# Typical share of goals scored before half-time in top leagues.
DEFAULT_HALF_TIME_SHARE = 0.45
# A referee's own average counts as this many "league average" matches.
REFEREE_PRIOR_MATCHES = 10


def _played(matches: list[MatchStats]) -> list[MatchStats]:
    return [m for m in matches if m.played]


def half_time_share(matches: list[MatchStats]) -> float:
    """Share of a league's goals that come before the break."""
    full = half = 0
    for m in _played(matches):
        if m.home_goals_ht is None or m.away_goals_ht is None:
            continue
        full += (m.home_goals or 0) + (m.away_goals or 0)
        half += m.home_goals_ht + m.away_goals_ht
    return half / full if full else DEFAULT_HALF_TIME_SHARE


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


@dataclass(frozen=True)
class _LeagueContext:
    """What every fixture of a league-season shares: computed once per request."""

    ratings: LeagueRatings
    played: list[MatchStats]
    names: dict[str, str]
    stat_models: dict[str, tuple[CountRatings, float]]
    half_time_share: float


@dataclass
class MatchInsightsUseCase:
    teams: TeamRepository
    stats: MatchStatsRepository
    today: Callable[[], date] = field(default=date.today)
    _contexts: dict[tuple[str, str], _LeagueContext] = field(
        default_factory=dict, init=False, repr=False
    )

    def execute(self, match_id: int) -> MatchInsights | None:
        fixture = next(
            (f for f in self.teams.list_fixtures() if f.match_id == match_id), None
        )
        return self.for_fixture(fixture) if fixture else None

    def _context(self, fixture: Fixture) -> _LeagueContext:
        key = (fixture.competition, fixture.season_label)
        if key in self._contexts:
            return self._contexts[key]
        today = self.today()
        labels = _labels_up_to(fixture.season_label)
        history = self.teams.list_team_matches(labels, fixture.competition)
        league_stats = self.stats.list_match_stats(fixture.competition, labels)
        played = [m for m in _played(league_stats) if m.played_on <= today]
        names = learn_team_names(
            [
                f
                for f in self.teams.list_fixtures(fixture.competition)
                if f.season_label in labels
            ],
            league_stats,
        )
        stat_models = {}
        for stat, (home_column, away_column, _) in STATS.items():
            records = _records(played, home_column, away_column)
            if records:
                stat_models[stat] = (
                    count_ratings(records, today),
                    dispersion([r.value_for for r in records]),
                )
        context = _LeagueContext(
            ratings=team_ratings([_record(m) for m in history], today),
            played=played,
            names=names,
            stat_models=stat_models,
            half_time_share=half_time_share(played),
        )
        self._contexts[key] = context
        return context

    def for_fixture(self, fixture: Fixture) -> MatchInsights:
        context = self._context(fixture)
        result = predict(context.ratings, fixture.home_team, fixture.away_team)
        home_name = context.names.get(fixture.home_team, fixture.home_team)
        away_name = context.names.get(fixture.away_team, fixture.away_team)
        played = [m for m in context.played if m.played_on < fixture.kickoff.date()]
        upcoming = self.stats.find_upcoming(
            fixture.competition, fixture.kickoff.date(), home_name, away_name
        )

        market: tuple[float, float, float] | None = None
        if (
            upcoming
            and upcoming.odds_home
            and upcoming.odds_draw
            and upcoming.odds_away
        ):
            home, draw, away = implied_probabilities(
                upcoming.odds_home, upcoming.odds_draw, upcoming.odds_away
            )
            market = (home, draw, away)
        model = (result.home_win, result.draw, result.away_win)
        consensus = (
            (
                (model[0] + market[0]) / 2,
                (model[1] + market[1]) / 2,
                (model[2] + market[2]) / 2,
            )
            if market
            else model
        )

        matrix = score_matrix(result.expected_home, result.expected_away)
        cells = [(h, a, p) for h, row in enumerate(matrix) for a, p in enumerate(row)]
        referee = _referee(upcoming.referee if upcoming else None, played)

        stats = {}
        for stat, (ratings, spread) in context.stat_models.items():
            multiplier = referee.multiplier if (stat == "yellows" and referee) else 1.0
            stats[stat] = stat_prediction(
                ratings,
                home_name,
                away_name,
                dispersion=spread,
                lines=STATS[stat][2],
                multiplier=multiplier,
            )

        share = context.half_time_share
        half = score_matrix(
            result.expected_home * share, result.expected_away * share, rho=0.0
        )
        half_cells = [
            (h, a, p) for h, row in enumerate(half) for a, p in enumerate(row)
        ]
        meetings = [
            m
            for m in reversed(played)
            if {m.home_team, m.away_team} == {home_name, away_name}
        ]
        return MatchInsights(
            fixture=fixture,
            result=result,
            market=market,
            consensus=consensus,
            goals_over={
                line: sum(p for h, a, p in cells if h + a > line) for line in GOAL_LINES
            },
            home_clean_sheet=sum(p for h, a, p in cells if a == 0),
            away_clean_sheet=sum(p for h, a, p in cells if h == 0),
            half_time=(
                sum(p for h, a, p in half_cells if h > a),
                sum(p for h, a, p in half_cells if h == a),
                sum(p for h, a, p in half_cells if h < a),
            ),
            stats=stats,
            referee=referee,
            head_to_head=meetings[:HEAD_TO_HEAD],
            home_recent=list(reversed(_involving(played, home_name)))[:RECENT],
            away_recent=list(reversed(_involving(played, away_name)))[:RECENT],
            home_name=home_name,
            away_name=away_name,
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


@dataclass(frozen=True)
class Pick:
    fixture: Fixture
    category: str
    label: str
    probability: float


@dataclass(frozen=True)
class Highlights:
    window_start: datetime
    window_end: datetime
    picks: list[Pick]


# The next round: from the first upcoming kick-off, a long weekend.
ROUND_DAYS = 4
CATEGORY_LINES = {"corners": (8.5, 9.5), "yellows": (3.5, 4.5)}
STAT_WORDS = {"corners": "córners", "yellows": "amarillas"}


def _number(value: float) -> str:
    return str(value).replace(".", ",")


@dataclass
class HighlightsUseCase:
    """The most likely outcomes of the next round, by category."""

    teams: TeamRepository
    stats: MatchStatsRepository
    shots: ShotRepository
    now: Callable[[], datetime] = field(default=datetime.now)

    def execute(self, per_category: int = 5) -> Highlights:
        start = self.now()
        upcoming = [f for f in self.teams.list_fixtures(start=start) if not f.played]
        if not upcoming:
            return Highlights(start, start, [])
        first = upcoming[0].kickoff
        window_start = datetime.combine(first.date(), datetime.min.time())
        window_end = window_start + timedelta(days=ROUND_DAYS)
        fixtures = [f for f in upcoming if f.kickoff < window_end]

        insights_use_case = MatchInsightsUseCase(
            self.teams, self.stats, lambda: start.date()
        )
        rosters: dict[tuple[str, str], list[RosterEntry]] = {}
        picks: list[Pick] = []
        for fixture in fixtures:
            insights = insights_use_case.for_fixture(fixture)
            picks += self._fixture_picks(insights)
            key = (fixture.competition, fixture.season_label)
            if key not in rosters:
                rosters[key] = self.shots.list_rosters(
                    fixture.competition, _labels_up_to(fixture.season_label)
                )
            picks += self._scorer_picks(insights, rosters[key])

        ranked: list[Pick] = []
        for category in ("result", "goals", "corners", "cards", "scorers"):
            best_per_fixture: dict[int, Pick] = {}
            for pick in picks:
                if pick.category != category:
                    continue
                kept = best_per_fixture.get(pick.fixture.match_id)
                if kept is None or pick.probability > kept.probability:
                    best_per_fixture[pick.fixture.match_id] = pick
            ranked += sorted(best_per_fixture.values(), key=lambda p: -p.probability)[
                :per_category
            ]
        return Highlights(window_start, window_end, ranked)

    @staticmethod
    def _fixture_picks(insights: MatchInsights) -> list[Pick]:
        fixture = insights.fixture
        home, away = fixture.home_team, fixture.away_team
        p_home, p_draw, p_away = insights.consensus
        picks = [
            Pick(fixture, "result", f"Gana {home}", p_home),
            Pick(fixture, "result", f"Gana {away}", p_away),
        ]
        # Headline markets only: "over 1.5 goals" or "fewer than 6.5 cards" are
        # almost always likely and tell nobody anything.
        for line in (2.5,):
            over = insights.goals_over[line]
            picks += [
                Pick(fixture, "goals", f"Más de {_number(line)} goles", over),
                Pick(fixture, "goals", f"Menos de {_number(line)} goles", 1 - over),
            ]
        btts = insights.result.both_teams_score
        picks += [
            Pick(fixture, "goals", "Marcan ambos", btts),
            Pick(fixture, "goals", "No marcan ambos", 1 - btts),
        ]
        for stat, category in (("corners", "corners"), ("yellows", "cards")):
            prediction = insights.stats.get(stat)
            if prediction is None:
                continue
            word = STAT_WORDS[stat]
            for line in CATEGORY_LINES[stat]:
                stat_over = prediction.over.get(line)
                if stat_over is None:
                    continue
                picks += [
                    Pick(
                        fixture, category, f"Más de {_number(line)} {word}", stat_over
                    ),
                    Pick(
                        fixture,
                        category,
                        f"Menos de {_number(line)} {word}",
                        1 - stat_over,
                    ),
                ]
            picks += [
                Pick(fixture, category, f"{home} con más {word}", prediction.home_more),
                Pick(fixture, category, f"{away} con más {word}", prediction.away_more),
            ]
        return [pick for pick in picks if pick.probability >= 0.5]

    @staticmethod
    def _scorer_picks(
        insights: MatchInsights, rosters: list[RosterEntry]
    ) -> list[Pick]:
        from player_scouting.application.use_cases.player_markets import _team_lines

        fixture = insights.fixture
        kickoff = fixture.kickoff.date()
        lines = _team_lines(
            fixture.home_team, rosters, kickoff, insights.result.expected_home
        ) + _team_lines(
            fixture.away_team, rosters, kickoff, insights.result.expected_away
        )
        if not lines:
            return []
        best = max(lines, key=lambda line: line.props.goal)
        return [Pick(fixture, "scorers", f"{best.name} marca", best.props.goal)]


@dataclass(frozen=True)
class MarketBenchmark:
    matches: int
    model_brier: float
    market_brier: float
    consensus_brier: float
    model_accuracy: float
    market_accuracy: float


def _average(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        (first[0] + second[0]) / 2,
        (first[1] + second[1]) / 2,
        (first[2] + second[2]) / 2,
    )


def _hit(probabilities: tuple[float, float, float], outcome: int) -> bool:
    return max(range(3), key=lambda i: probabilities[i]) == outcome


def _brier3(probabilities: tuple[float, float, float], outcome: int) -> float:
    return sum(
        (p - (1.0 if i == outcome else 0.0)) ** 2 for i, p in enumerate(probabilities)
    )


@dataclass
class MarketBenchmarkUseCase:
    """Our 1X2 model vs bookmakers' closing odds on exactly the same matches.

    Walk-forward like the other backtests: each match is forecast only with the
    matches played before it.
    """

    teams: TeamRepository
    stats: MatchStatsRepository
    minimum_history: int = 30

    def execute(self, season_label: str) -> MarketBenchmark:
        labels = _labels_up_to(season_label)
        rows: list[
            tuple[tuple[float, float, float], tuple[float, float, float], int]
        ] = []
        fixtures = [
            f
            for f in self.teams.list_fixtures()
            if f.played and f.season_label == season_label
        ]
        for competition in sorted({f.competition for f in fixtures}):
            history = self.teams.list_team_matches(labels, competition)
            league_stats = self.stats.list_match_stats(competition, labels)
            names = learn_team_names(
                [
                    f
                    for f in self.teams.list_fixtures(competition)
                    if f.season_label in labels
                ],
                league_stats,
            )
            odds = {
                (m.played_on, m.home_team, m.away_team): m
                for m in league_stats
                if m.odds_home and m.odds_draw and m.odds_away
            }
            ratings_by_day: dict[date, LeagueRatings] = {}
            for fixture in (f for f in fixtures if f.competition == competition):
                day = fixture.kickoff.date()
                earlier = [m for m in history if m.played_on < day]
                if len({m.match_id for m in earlier}) < self.minimum_history:
                    continue
                home = names.get(fixture.home_team, fixture.home_team)
                away = names.get(fixture.away_team, fixture.away_team)
                match = next(
                    (
                        odds[(day + timedelta(days=offset), home, away)]
                        for offset in (0, -1, 1)
                        if (day + timedelta(days=offset), home, away) in odds
                    ),
                    None,
                )
                if match is None:
                    continue
                if day not in ratings_by_day:
                    ratings_by_day[day] = team_ratings(
                        [_record(m) for m in earlier], day
                    )
                prediction = predict(
                    ratings_by_day[day], fixture.home_team, fixture.away_team
                )
                model = (prediction.home_win, prediction.draw, prediction.away_win)
                assert match.odds_home and match.odds_draw and match.odds_away
                h, d, a = implied_probabilities(
                    match.odds_home, match.odds_draw, match.odds_away
                )
                assert fixture.home_goals is not None and fixture.away_goals is not None
                outcome = (
                    0
                    if fixture.home_goals > fixture.away_goals
                    else 1
                    if fixture.home_goals == fixture.away_goals
                    else 2
                )
                rows.append((model, (h, d, a), outcome))
        if not rows:
            return MarketBenchmark(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        count = len(rows)

        return MarketBenchmark(
            matches=count,
            model_brier=sum(_brier3(m, o) for m, _, o in rows) / count,
            market_brier=sum(_brier3(k, o) for _, k, o in rows) / count,
            consensus_brier=sum(_brier3(_average(m, k), o) for m, k, o in rows) / count,
            model_accuracy=sum(_hit(m, o) for m, _, o in rows) / count,
            market_accuracy=sum(_hit(k, o) for _, k, o in rows) / count,
        )
