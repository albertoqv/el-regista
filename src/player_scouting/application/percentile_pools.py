from __future__ import annotations

from collections import defaultdict
from collections.abc import Hashable, Iterable

from player_scouting.domain.percentiles import MetricPercentile, rank_rates, style_rates
from player_scouting.domain.statistics import Statistics

# Peers need this share of the busiest player's minutes, and at least one match.
MINIMUM_MINUTES_SHARE = 0.3
MINIMUM_MINUTES_FLOOR = 90


def minimum_minutes(statistics: Iterable[Statistics]) -> int:
    busiest = max((s.minutes_played for s in statistics), default=0)
    return max(MINIMUM_MINUTES_FLOOR, int(busiest * MINIMUM_MINUTES_SHARE))


def pool_percentiles[Key: Hashable](
    pools: dict[Hashable, list[tuple[Key, Statistics]]],
    targets: set[Key],
    extra_rates: dict[Key, dict[str, float]] | None = None,
) -> dict[Key, dict[str, MetricPercentile]]:
    """Percentile profile of each target inside its own pool.

    A pool is the set of players compared together (same league, season and
    position). Peers need enough minutes; a target is ranked even without them.
    `extra_rates` adds metrics from other sources (e.g. shot profiles).
    """
    extra = extra_rates or {}
    profiles: dict[Key, dict[str, MetricPercentile]] = {}
    for members in pools.values():
        threshold = minimum_minutes(stats for _, stats in members)
        rates = {key: style_rates(stats) | extra.get(key, {}) for key, stats in members}
        eligible = [
            rates[key] for key, stats in members if stats.minutes_played >= threshold
        ]
        for key, statistics in members:
            if key not in targets:
                continue
            enough = statistics.minutes_played >= threshold
            peers = eligible if enough else [*eligible, rates[key]]
            profiles[key] = rank_rates(rates[key], peers)
    return profiles


def group_into_pools[Key: Hashable](
    members: Iterable[tuple[Hashable, Key, Statistics]],
) -> dict[Hashable, list[tuple[Key, Statistics]]]:
    pools: dict[Hashable, list[tuple[Key, Statistics]]] = defaultdict(list)
    for pool, key, statistics in members:
        pools[pool].append((key, statistics))
    return pools
