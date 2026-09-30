from __future__ import annotations

import math
from dataclasses import dataclass, replace

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
BOX_DEPTH = 16.5
BOX_WIDTH = 40.32
# "Tramo final": the last quarter of an hour plus stoppage time.
LATE_MINUTE = 75

GOAL = "Goal"
OWN_GOAL = "OwnGoal"


@dataclass(frozen=True)
class Shot:
    """One shot as Understat records it; x runs towards the goal, y across."""

    shot_id: int
    match_id: int
    understat_player_id: int
    player_name: str
    minute: int
    result: str
    x: float
    y: float
    xg: float
    situation: str
    shot_type: str
    home: bool
    assisted_by: str | None
    decisive: bool = False

    @property
    def is_goal(self) -> bool:
        return self.result == GOAL


def distance_to_goal(x: float, y: float) -> float:
    return math.hypot((1 - x) * PITCH_LENGTH, (y - 0.5) * PITCH_WIDTH)


def is_outside_box(x: float, y: float) -> bool:
    beyond_line = (1 - x) * PITCH_LENGTH > BOX_DEPTH
    out_wide = abs(y - 0.5) * PITCH_WIDTH > BOX_WIDTH / 2
    return beyond_line or out_wide


def mark_decisive_goals(shots: list[Shot]) -> list[Shot]:
    """Flags the goals that equalise or put the scorer's team ahead.

    Replays the match in minute order. Own goals change the score (for the
    other side) but are never decisive for the player who scored them.
    """
    home_goals = away_goals = 0
    marked = []
    for shot in sorted(shots, key=lambda s: (s.minute, s.shot_id)):
        decisive = False
        if shot.result == GOAL:
            own, other = (
                (home_goals, away_goals) if shot.home else (away_goals, home_goals)
            )
            # Level it (was one behind) or go ahead (was level).
            decisive = other - 1 <= own <= other
            if shot.home:
                home_goals += 1
            else:
                away_goals += 1
        elif shot.result == OWN_GOAL:
            if shot.home:
                away_goals += 1
            else:
                home_goals += 1
        marked.append(replace(shot, decisive=decisive))
    return marked


@dataclass(frozen=True)
class ShotTotals:
    """A player's shots in one league season (penalties excluded)."""

    shots: int
    np_xg: float
    np_goals: int
    late_goals: int
    headed_goals: int
    outside_box_goals: int
    set_piece_goals: int


def shot_rates(totals: ShotTotals, minutes: int) -> dict[str, float]:
    """Shot profile as rates: counts per 90 minutes, quality per shot."""
    if minutes <= 0:
        return {}
    per_90 = 90 / minutes
    rates = {
        "late_goals": totals.late_goals * per_90,
        "headed_goals": totals.headed_goals * per_90,
        "outside_box_goals": totals.outside_box_goals * per_90,
        "set_piece_goals": totals.set_piece_goals * per_90,
        "finishing": (totals.np_goals - totals.np_xg) * per_90,
    }
    if totals.shots:
        rates["npxg_per_shot"] = totals.np_xg / totals.shots
    return rates
