from __future__ import annotations

from dataclasses import dataclass

from player_scouting.domain.statistics import Statistics

# Per-90 rates used for scouting profiles (Wyscout-style radar).
PERCENTILE_METRICS = (
    "goals",
    "assists",
    "expected_goals",
    "expected_assists",
    "shots",
    "shots_on_target",
    "key_passes",
    "xg_chain",
    "xg_buildup",
    "passes_completed",
    "dribbles_completed",
    "tackles_won",
    "interceptions",
    "fouls_won",
)


@dataclass(frozen=True)
class MetricPercentile:
    per_90: float
    percentile: int


def per_90(statistics: Statistics, metric: str) -> float:
    if statistics.minutes_played == 0:
        return 0.0
    return float(getattr(statistics, metric)) * 90 / statistics.minutes_played


def style_rates(statistics: Statistics) -> dict[str, float]:
    return {metric: per_90(statistics, metric) for metric in PERCENTILE_METRICS}


def rank_rates(
    target: dict[str, float], peers: list[dict[str, float]]
) -> dict[str, MetricPercentile]:
    """Percentile of each target rate among the peers that have that rate.

    Ties count half. Metrics nobody recorded (the source did not track them)
    are left out.
    """
    profile = {}
    for metric, value in target.items():
        rates = [peer[metric] for peer in peers if metric in peer]
        if not rates or not any(rates):
            continue
        below = sum(rate < value for rate in rates)
        equal = sum(rate == value for rate in rates)
        share = (below + equal / 2) / len(rates)
        profile[metric] = MetricPercentile(
            per_90=round(value, 2), percentile=int(share * 100 + 0.5)
        )
    return profile


def percentile_profile(
    target: Statistics, peers: list[Statistics]
) -> dict[str, MetricPercentile]:
    """Percentile of the target's per-90 rates among its peers."""
    return rank_rates(style_rates(target), [style_rates(peer) for peer in peers])
