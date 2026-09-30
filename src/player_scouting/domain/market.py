from __future__ import annotations


def implied_probabilities(*odds: float) -> tuple[float, ...]:
    """Bookmaker odds -> probabilities without the margin (proportional method)."""
    raw = [1 / price for price in odds]
    total = sum(raw)
    return tuple(value / total for value in raw)
