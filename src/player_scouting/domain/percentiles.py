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


def percentile_profile(
    target: Statistics, peers: list[Statistics]
) -> dict[str, MetricPercentile]:
    """Percentile of the target's per-90 rate among peers (ties count half).

    Metrics nobody recorded (the source did not track them) are left out.
    """
    profile = {}
    for metric in PERCENTILE_METRICS:
        rates = [per_90(peer, metric) for peer in peers]
        if not any(rates):
            continue
        value = per_90(target, metric)
        below = sum(rate < value for rate in rates)
        equal = sum(rate == value for rate in rates)
        share = (below + equal / 2) / len(rates)
        profile[metric] = MetricPercentile(
            per_90=round(value, 2), percentile=int(share * 100 + 0.5)
        )
    return profile
