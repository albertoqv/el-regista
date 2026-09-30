"""Match forecasts: a Dixon-Coles adjusted Poisson model on xG-based strengths.

Each team gets an attack and a defence multiplier (1.0 = league average),
estimated from its matches with:
- a blend of expected goals (stable, measures chances) and real goals;
- exponential time decay, so current form weighs more than August;
- opponent adjustment (scoring against a good defence counts more);
- shrinkage towards average with a few pseudo-matches, so two lucky games do
  not turn a team into a giant.
Expected goals of a fixture = league venue average x attack x opponent defence.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

# Weight of expected goals vs real goals in a team's "performance".
XG_WEIGHT = 0.7
DEFAULT_HALF_LIFE_DAYS = 120
PRIOR_MATCHES = 4.0
# League venue averages start from typical top-flight values (goals per team
# per match) and move towards what this league actually shows.
PRIOR_HOME_GOALS = 1.5
PRIOR_AWAY_GOALS = 1.2
PRIOR_VENUE_MATCHES = 20.0
DIXON_COLES_RHO = -0.1
MAX_GOALS = 10
ITERATIONS = 8


@dataclass(frozen=True)
class TeamMatchRecord:
    """One match seen from one team's side."""

    team: str
    opponent: str
    home: bool
    played_on: date
    goals_for: int
    goals_against: int
    xg_for: float
    xg_against: float


@dataclass(frozen=True)
class LeagueRatings:
    home_goals: float
    away_goals: float
    attack: dict[str, float]
    defence: dict[str, float]

    def attack_of(self, team: str) -> float:
        return self.attack.get(team, 1.0)

    def defence_of(self, team: str) -> float:
        return self.defence.get(team, 1.0)


@dataclass(frozen=True)
class MatchPrediction:
    home_win: float
    draw: float
    away_win: float
    expected_home: float
    expected_away: float
    scorelines: tuple[tuple[int, int, float], ...]
    over_2_5: float
    both_teams_score: float


def _performance(goals: int, xg: float) -> float:
    return XG_WEIGHT * xg + (1 - XG_WEIGHT) * goals


def _weight(played_on: date, today: date, half_life_days: float) -> float:
    age = max((today - played_on).days, 0)
    return 0.5 ** (age / half_life_days)


def team_ratings(
    matches: list[TeamMatchRecord],
    today: date,
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
) -> LeagueRatings:
    weighted = [
        (m, _weight(m.played_on, today, half_life_days))
        for m in matches
        if m.played_on <= today
    ]

    def venue_average(home: bool, prior: float) -> float:
        total = sum(
            w * _performance(m.goals_for, m.xg_for)
            for m, w in weighted
            if m.home == home
        )
        weights = sum(w for m, w in weighted if m.home == home)
        return (total + PRIOR_VENUE_MATCHES * prior) / (weights + PRIOR_VENUE_MATCHES)

    home_goals = venue_average(True, PRIOR_HOME_GOALS)
    away_goals = venue_average(False, PRIOR_AWAY_GOALS)
    teams = {m.team for m, _ in weighted}
    attack = dict.fromkeys(teams, 1.0)
    defence = dict.fromkeys(teams, 1.0)

    for _ in range(ITERATIONS):
        attack_sum: dict[str, float] = defaultdict(float)
        defence_sum: dict[str, float] = defaultdict(float)
        weight_sum: dict[str, float] = defaultdict(float)
        for match, w in weighted:
            scored_base = home_goals if match.home else away_goals
            conceded_base = away_goals if match.home else home_goals
            # What an average team would score here, given this opponent.
            expected_for = scored_base * defence.get(match.opponent, 1.0)
            expected_against = conceded_base * attack.get(match.opponent, 1.0)
            attack_sum[match.team] += (
                w * _performance(match.goals_for, match.xg_for) / expected_for
            )
            defence_sum[match.team] += (
                w
                * _performance(match.goals_against, match.xg_against)
                / expected_against
            )
            weight_sum[match.team] += w
        attack = {
            team: (attack_sum[team] + PRIOR_MATCHES)
            / (weight_sum[team] + PRIOR_MATCHES)
            for team in teams
        }
        defence = {
            team: (defence_sum[team] + PRIOR_MATCHES)
            / (weight_sum[team] + PRIOR_MATCHES)
            for team in teams
        }
    return LeagueRatings(home_goals, away_goals, attack, defence)


def _poisson(k: int, rate: float) -> float:
    return math.exp(-rate) * rate**k / math.factorial(k)


def _dixon_coles(
    home: int, away: int, rate_home: float, rate_away: float, rho: float
) -> float:
    """Low-score correction: real football has more 0-0 and 1-1 than Poisson."""
    if home == 0 and away == 0:
        return 1 - rate_home * rate_away * rho
    if home == 0 and away == 1:
        return 1 + rate_home * rho
    if home == 1 and away == 0:
        return 1 + rate_away * rho
    if home == 1 and away == 1:
        return 1 - rho
    return 1.0


def score_matrix(
    rate_home: float, rate_away: float, rho: float = DIXON_COLES_RHO
) -> list[list[float]]:
    matrix = [
        [
            _poisson(h, rate_home)
            * _poisson(a, rate_away)
            * _dixon_coles(h, a, rate_home, rate_away, rho)
            for a in range(MAX_GOALS + 1)
        ]
        for h in range(MAX_GOALS + 1)
    ]
    total = sum(sum(row) for row in matrix)
    return [[cell / total for cell in row] for row in matrix]


def predict(ratings: LeagueRatings, home: str, away: str) -> MatchPrediction:
    rate_home = ratings.home_goals * ratings.attack_of(home) * ratings.defence_of(away)
    rate_away = ratings.away_goals * ratings.attack_of(away) * ratings.defence_of(home)
    matrix = score_matrix(rate_home, rate_away)
    cells = [
        (h, a, matrix[h][a]) for h in range(MAX_GOALS + 1) for a in range(MAX_GOALS + 1)
    ]
    return MatchPrediction(
        home_win=sum(p for h, a, p in cells if h > a),
        draw=sum(p for h, a, p in cells if h == a),
        away_win=sum(p for h, a, p in cells if h < a),
        expected_home=rate_home,
        expected_away=rate_away,
        scorelines=tuple(sorted(cells, key=lambda cell: -cell[2])[:5]),
        over_2_5=sum(p for h, a, p in cells if h + a > 2),
        both_teams_score=sum(p for h, a, p in cells if h > 0 and a > 0),
    )
