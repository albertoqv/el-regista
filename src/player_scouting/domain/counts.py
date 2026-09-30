"""Match counts other than goals: corners, cards, fouls, shots...

Same idea as the goals model (domain/prediction.py): each team gets a "for"
and an "against" multiplier (1.0 = league average) from its matches, with time
decay, opponent and venue adjustment and shrinkage. Counts such as corners or
cards vary more than a Poisson allows, so each side is a negative binomial
whose dispersion is estimated from the league.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

HALF_LIFE_DAYS = 120
PRIOR_MATCHES = 3.0
PRIOR_VENUE_MATCHES = 20.0
ITERATIONS = 8
MAX_COUNT = 80
# No overdispersion: a negative binomial this wide is a Poisson in practice.
POISSON_LIKE = 1000.0


@dataclass(frozen=True)
class CountRecord:
    team: str
    opponent: str
    home: bool
    played_on: date
    value_for: float
    value_against: float


@dataclass(frozen=True)
class CountRatings:
    home_average: float
    away_average: float
    for_: dict[str, float]
    against: dict[str, float]


@dataclass(frozen=True)
class StatPrediction:
    expected_home: float
    expected_away: float
    expected_total: float
    home_more: float
    equal: float
    away_more: float
    over: dict[float, float]
    total_distribution: tuple[float, ...]


def _weight(played_on: date, today: date) -> float:
    return 0.5 ** (max((today - played_on).days, 0) / HALF_LIFE_DAYS)


def count_ratings(records: list[CountRecord], today: date) -> CountRatings:
    weighted = [
        (r, _weight(r.played_on, today)) for r in records if r.played_on <= today
    ]
    overall = [r.value_for for r, _ in weighted]
    prior = sum(overall) / len(overall) if overall else 1.0

    def venue(home: bool) -> float:
        total = sum(w * r.value_for for r, w in weighted if r.home == home)
        weights = sum(w for r, w in weighted if r.home == home)
        return (total + PRIOR_VENUE_MATCHES * prior) / (weights + PRIOR_VENUE_MATCHES)

    home_average, away_average = venue(True), venue(False)
    teams = {r.team for r, _ in weighted}
    for_ = dict.fromkeys(teams, 1.0)
    against = dict.fromkeys(teams, 1.0)
    for _ in range(ITERATIONS):
        sums_for: dict[str, float] = defaultdict(float)
        sums_against: dict[str, float] = defaultdict(float)
        weights: dict[str, float] = defaultdict(float)
        for record, w in weighted:
            base_for = home_average if record.home else away_average
            base_against = away_average if record.home else home_average
            expected_for = max(base_for * against.get(record.opponent, 1.0), 1e-6)
            expected_against = max(base_against * for_.get(record.opponent, 1.0), 1e-6)
            sums_for[record.team] += w * record.value_for / expected_for
            sums_against[record.team] += w * record.value_against / expected_against
            weights[record.team] += w
        for_ = {
            t: (sums_for[t] + PRIOR_MATCHES) / (weights[t] + PRIOR_MATCHES)
            for t in teams
        }
        against = {
            t: (sums_against[t] + PRIOR_MATCHES) / (weights[t] + PRIOR_MATCHES)
            for t in teams
        }
    return CountRatings(home_average, away_average, for_, against)


def dispersion(values: list[float]) -> float:
    """Negative binomial k by the method of moments (sample variance)."""
    if len(values) < 2:
        return POISSON_LIKE
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    if variance <= mean:
        return POISSON_LIKE
    return min(mean**2 / (variance - mean), POISSON_LIKE)


def negative_binomial_pmf(k: int, mean: float, dispersion: float) -> float:
    if mean <= 0:
        return 1.0 if k == 0 else 0.0
    p = dispersion / (dispersion + mean)
    log = (
        math.lgamma(k + dispersion)
        - math.lgamma(dispersion)
        - math.lgamma(k + 1)
        + dispersion * math.log(p)
        + k * math.log(1 - p)
    )
    return math.exp(log)


def _distribution(mean: float, k: float) -> list[float]:
    values = [negative_binomial_pmf(n, mean, k) for n in range(MAX_COUNT + 1)]
    total = sum(values)
    return [v / total for v in values]


def stat_prediction(
    ratings: CountRatings,
    home: str,
    away: str,
    dispersion: float,
    lines: tuple[float, ...],
    multiplier: float = 1.0,
) -> StatPrediction:
    """Both sides as independent negative binomials; `multiplier` scales the
    whole match (e.g. a referee who shows more cards than average)."""
    mean_home = (
        ratings.home_average
        * ratings.for_.get(home, 1.0)
        * ratings.against.get(away, 1.0)
        * multiplier
    )
    mean_away = (
        ratings.away_average
        * ratings.for_.get(away, 1.0)
        * ratings.against.get(home, 1.0)
        * multiplier
    )
    home_dist = _distribution(mean_home, dispersion)
    away_dist = _distribution(mean_away, dispersion)
    total = [0.0] * (2 * MAX_COUNT + 1)
    home_more = equal = away_more = 0.0
    for h, ph in enumerate(home_dist):
        for a, pa in enumerate(away_dist):
            p = ph * pa
            total[h + a] += p
            if h > a:
                home_more += p
            elif h == a:
                equal += p
            else:
                away_more += p
    return StatPrediction(
        expected_home=mean_home,
        expected_away=mean_away,
        expected_total=mean_home + mean_away,
        home_more=home_more,
        equal=equal,
        away_more=away_more,
        over={line: sum(p for n, p in enumerate(total) if n > line) for line in lines},
        total_distribution=tuple(total[: 2 * MAX_COUNT + 1]),
    )
