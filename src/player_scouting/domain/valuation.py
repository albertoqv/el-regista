"""What the market would pay for a player, from what he does: an explainable model.

A ridge regression on the logarithm of the market value (Transfermarkt), so each
input multiplies the price: a stronger league, more goals, the right age. Every
estimate breaks down into factors against an average player ("x1.8 for the league"),
and the error is measured on players the model did not learn from.

Pure Python like the forecasting models: a few dozen inputs, solved exactly.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

# Ridge penalty on the standardised inputs: steadies leagues with few players.
PENALTY = 1.0
# A league with fewer valued players than this is pooled as "another league".
MIN_LEAGUE_PLAYERS = 20
OTHER_LEAGUE = "Otra liga"
# One player in five is kept out of the fit to measure the error honestly.
HOLDOUT_EVERY = 5


@dataclass(frozen=True)
class ValuationInput:
    player_id: int
    age: float
    position: str
    league: str | None
    # His last club season: minutes, and goals and assists per 90.
    minutes: int
    goals_per90: float
    assists_per90: float
    europe_appearances: int
    national_appearances: int
    # What Transfermarkt says today; None = only estimated, not learnt from.
    market_value_eur: int | None


@dataclass(frozen=True)
class ValueFactor:
    label: str
    factor: float


@dataclass(frozen=True)
class ValueEstimate:
    player_id: int
    estimate_eur: int
    # Against the average player; multiplied together they give the estimate.
    factors: tuple[ValueFactor, ...]


@dataclass(frozen=True)
class ValuationReport:
    estimates: list[ValueEstimate]
    average_eur: int
    # Median of |estimate / market - 1| on players left out of the fit.
    median_error: float
    samples: int


_NUMERIC: tuple[tuple[str, Callable[[ValuationInput], float]], ...] = (
    ("Edad", lambda p: p.age),
    ("Edad", lambda p: p.age**2),
    ("Minutos", lambda p: math.log1p(p.minutes)),
    ("Goles", lambda p: p.goals_per90),
    ("Asistencias", lambda p: p.assists_per90),
    ("Europa", lambda p: math.log1p(p.europe_appearances)),
    ("Selección", lambda p: math.log1p(p.national_appearances)),
)


@dataclass(frozen=True)
class _Design:
    groups: list[str]
    means: list[float]
    scales: list[float]
    positions: list[str]
    leagues: list[str]

    def row(self, player: ValuationInput) -> list[float]:
        numeric = [
            (feature(player) - mean) / scale
            for (_, feature), mean, scale in zip(
                _NUMERIC, self.means, self.scales, strict=True
            )
        ]
        league = player.league if player.league in self.leagues else OTHER_LEAGUE
        return (
            [1.0]
            + numeric
            + [1.0 if player.position == p else 0.0 for p in self.positions]
            + [1.0 if league == name else 0.0 for name in self.leagues]
        )


def _design(players: list[ValuationInput]) -> _Design:
    means, scales = [], []
    for _, feature in _NUMERIC:
        values = [feature(p) for p in players]
        means.append(statistics.fmean(values))
        scales.append(statistics.pstdev(values) or 1.0)
    counts = Counter(p.league for p in players if p.league)
    leagues = sorted(name for name, n in counts.items() if n >= MIN_LEAGUE_PLAYERS)
    positions = sorted({p.position for p in players})
    groups = (
        ["intercept"]
        + [label for label, _ in _NUMERIC]
        + ["Posición"] * len(positions)
        + ["Liga"] * (len(leagues) + 1)
    )
    return _Design(groups, means, scales, positions, leagues + [OTHER_LEAGUE])


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (the system is small)."""
    size = len(vector)
    rows = [matrix[i][:] + [vector[i]] for i in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(rows[r][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        lead = rows[column][column]
        for r in range(column + 1, size):
            ratio = rows[r][column] / lead
            if ratio:
                for c in range(column, size + 1):
                    rows[r][c] -= ratio * rows[column][c]
    weights = [0.0] * size
    for r in range(size - 1, -1, -1):
        known = sum(rows[r][c] * weights[c] for c in range(r + 1, size))
        weights[r] = (rows[r][size] - known) / rows[r][r]
    return weights


def _fit(design: _Design, players: list[ValuationInput]) -> list[float]:
    rows = [design.row(p) for p in players]
    targets = [math.log(p.market_value_eur or 1) for p in players]
    size = len(rows[0])
    matrix = [[0.0] * size for _ in range(size)]
    vector = [0.0] * size
    for row, target in zip(rows, targets, strict=True):
        for i in range(size):
            if row[i]:
                vector[i] += row[i] * target
                for j in range(size):
                    matrix[i][j] += row[i] * row[j]
    for i in range(1, size):  # the intercept is not penalised
        matrix[i][i] += PENALTY
    return _solve(matrix, vector)


def _predict(design: _Design, weights: list[float], player: ValuationInput) -> float:
    return sum(w * x for w, x in zip(weights, design.row(player), strict=True))


def estimate_values(players: list[ValuationInput]) -> ValuationReport:
    valued = [p for p in players if p.market_value_eur]
    if not valued:
        return ValuationReport([], 0, 0.0, 0)

    # The honest error: fit without one player in five, measure on them.
    train = [p for p in valued if p.player_id % HOLDOUT_EVERY]
    held = [p for p in valued if not p.player_id % HOLDOUT_EVERY]
    if train and held:
        design = _design(train)
        weights = _fit(design, train)
        errors = [
            abs(math.exp(_predict(design, weights, p)) / (p.market_value_eur or 1) - 1)
            for p in held
        ]
        median_error = statistics.median(errors)
    else:
        median_error = 0.0

    design = _design(valued)
    weights = _fit(design, valued)
    rows = [design.row(p) for p in valued]
    column_means = [statistics.fmean(column) for column in zip(*rows, strict=True)]
    average_log = sum(w * m for w, m in zip(weights, column_means, strict=True))

    estimates = []
    for player in players:
        contributions: dict[str, float] = {}
        for group, weight, value, mean in zip(
            design.groups, weights, design.row(player), column_means, strict=True
        ):
            if group != "intercept":
                contributions[group] = contributions.get(group, 0.0) + weight * (
                    value - mean
                )
        factors = tuple(
            ValueFactor(label, round(math.exp(log_factor), 4))
            for label, log_factor in sorted(
                contributions.items(), key=lambda item: -abs(item[1])
            )
        )
        estimates.append(
            ValueEstimate(
                player_id=player.player_id,
                estimate_eur=round(math.exp(average_log + sum(contributions.values()))),
                factors=factors,
            )
        )
    return ValuationReport(
        estimates=estimates,
        average_eur=round(math.exp(average_log)),
        median_error=round(median_error, 4),
        samples=len(valued),
    )
