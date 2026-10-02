from __future__ import annotations

from dataclasses import dataclass

# Fewer shared metrics than this and the comparison says nothing about style.
MINIMUM_SHARED_METRICS = 5
# Leagues with only goals and assists still get a (basic) comparison.
BASIC_SHARED_METRICS = 2
# A metric is one of the target's strengths from this percentile up.
STRENGTH_PERCENTILE = 60
HIGHLIGHTS = 3


@dataclass(frozen=True)
class StyleSimilarity:
    percentage: int
    shared_strengths: tuple[str, ...]
    differences: tuple[str, ...]


def style_similarity(
    target: dict[str, int],
    candidate: dict[str, int],
    minimum_shared: int = MINIMUM_SHARED_METRICS,
) -> StyleSimilarity | None:
    """How alike two percentile profiles are: 100 minus the mean percentile gap.

    Percentiles already put every metric on the same 0-100 scale and discount
    league and position context, so a plain mean gap is easy to explain.
    """
    shared = [metric for metric in target if metric in candidate]
    if len(shared) < minimum_shared:
        return None

    gaps = {metric: abs(target[metric] - candidate[metric]) for metric in shared}
    mean_gap = sum(gaps.values()) / len(gaps)

    by_closeness = sorted(shared, key=lambda metric: (gaps[metric], -target[metric]))
    strengths = [m for m in by_closeness if target[m] >= STRENGTH_PERCENTILE]
    by_distance = sorted(shared, key=lambda metric: -gaps[metric])
    return StyleSimilarity(
        percentage=int(100 - mean_gap + 0.5),
        shared_strengths=tuple(strengths[:HIGHLIGHTS]),
        differences=tuple(m for m in by_distance[:2] if gaps[m] >= 20),
    )
