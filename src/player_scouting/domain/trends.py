"""A player's form match by match: threat (xG + xA) per 90 over the last games.

Per 90 over a rolling window counts minutes, so 45 minutes off the bench weigh
half a match. The direction compares the last window with everything before it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

DEFAULT_WINDOW = 5
# The recent level must move this much (share and absolute) to be a trend.
TREND_SHARE = 0.2
TREND_MINIMUM = 0.1

Direction = Literal["up", "down", "steady"]


@dataclass(frozen=True)
class MatchLine:
    played_on: date
    opponent: str
    home: bool
    minutes: int
    goals: int
    assists: int
    shots: int
    xg: float
    xa: float


@dataclass(frozen=True)
class TrendPoint:
    line: MatchLine
    rolling_per90: float


@dataclass(frozen=True)
class Trend:
    points: list[TrendPoint]
    window: int
    recent_per90: float | None
    earlier_per90: float | None
    direction: Direction | None
    goals_minus_xg: float


def _per90(lines: list[MatchLine]) -> float:
    minutes = sum(line.minutes for line in lines)
    return 90 * sum(line.xg + line.xa for line in lines) / minutes if minutes else 0.0


def build_trend(lines: list[MatchLine], window: int = DEFAULT_WINDOW) -> Trend:
    played = sorted(
        (line for line in lines if line.minutes > 0), key=lambda line: line.played_on
    )
    points = [
        TrendPoint(line, _per90(played[max(0, index - window + 1) : index + 1]))
        for index, line in enumerate(played)
    ]
    recent = played[-window:]
    earlier = played[:-window]
    recent_per90 = _per90(recent) if recent else None
    earlier_per90 = _per90(earlier) if earlier else None
    direction: Direction | None = None
    if (
        recent_per90 is not None
        and earlier_per90 is not None
        and len(earlier) >= window
    ):
        change = recent_per90 - earlier_per90
        if abs(change) >= TREND_MINIMUM and abs(change) >= TREND_SHARE * earlier_per90:
            direction = "up" if change > 0 else "down"
        else:
            direction = "steady"
    return Trend(
        points=points,
        window=window,
        recent_per90=recent_per90,
        earlier_per90=earlier_per90,
        direction=direction,
        goals_minus_xg=sum(line.goals - line.xg for line in played),
    )
