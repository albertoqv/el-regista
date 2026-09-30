"""Player markets: to score, to assist, to be booked, to have shots.

For each player:
- expected minutes = weighted average of his minutes in the team's last
  matches (latest weigh more; 0 when he did not play), so injuries, drops and
  rotations show up as soon as they happen;
- per-90 rates of xG, xA, shots and yellow cards, shrunk towards the average
  of his position so a few lucky minutes do not dominate;
- the match: `team_factor` = goals the model expects from his team in this
  fixture / what the team usually produces (a weak opponent lifts everyone).
Each count is then a Poisson with mean rate x minutes/90 x factor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MINUTES_DECAY = 0.8
PRIOR_MINUTES = 900.0

# Per-90 position averages in the top five leagues (Understat-sized).
_PRIORS = {
    #              xG    xA    shots yellows
    "forward": (0.33, 0.12, 2.6, 0.12),
    "attacking": (0.20, 0.17, 1.9, 0.14),
    "midfield": (0.08, 0.08, 0.9, 0.22),
    "defence": (0.04, 0.05, 0.5, 0.19),
    "goalkeeper": (0.0, 0.0, 0.0, 0.05),
}


@dataclass(frozen=True)
class Appearance:
    minutes: int
    xg: float
    xa: float
    shots: int
    yellow: int
    position: str


@dataclass(frozen=True)
class PlayerProps:
    expected_minutes: float
    expected_goals: float
    goal: float
    assist: float
    card: float
    shots_1: float
    shots_2: float


def position_group(position: str) -> str:
    if position == "GK":
        return "goalkeeper"
    if position.startswith("FW"):
        return "forward"
    if position.startswith("AM"):
        return "attacking"
    if position.startswith("D") and not position.startswith("DM"):
        return "defence"
    return "midfield"


def expected_minutes(recent_minutes: list[int]) -> float:
    """Latest match first; 0 for matches he missed."""
    weights = [MINUTES_DECAY**index for index in range(len(recent_minutes))]
    if not weights:
        return 0.0
    return sum(w * m for w, m in zip(weights, recent_minutes, strict=True)) / sum(
        weights
    )


def _main_position(history: list[Appearance]) -> str:
    counts: dict[str, int] = {}
    for appearance in history:
        if appearance.position != "Sub":
            counts[appearance.position] = counts.get(appearance.position, 0) + 1
    return max(counts, key=lambda p: counts[p]) if counts else "MC"


def _rate(total: float, minutes: float, prior_per_90: float) -> float:
    return (total + prior_per_90 * PRIOR_MINUTES / 90) / (minutes + PRIOR_MINUTES) * 90


def player_props(
    history: list[Appearance],
    minutes: float,
    team_factor: float,
    card_factor: float,
) -> PlayerProps:
    prior_xg, prior_xa, prior_shots, prior_yellow = _PRIORS[
        position_group(_main_position(history))
    ]
    played = sum(a.minutes for a in history)
    share = minutes / 90
    expected_goals = (
        _rate(sum(a.xg for a in history), played, prior_xg) * share * team_factor
    )
    expected_assists = (
        _rate(sum(a.xa for a in history), played, prior_xa) * share * team_factor
    )
    expected_shots = (
        _rate(sum(a.shots for a in history), played, prior_shots) * share * team_factor
    )
    expected_cards = (
        _rate(sum(a.yellow for a in history), played, prior_yellow)
        * share
        * card_factor
    )
    return PlayerProps(
        expected_minutes=minutes,
        expected_goals=expected_goals,
        goal=1 - math.exp(-expected_goals),
        assist=1 - math.exp(-expected_assists),
        card=1 - math.exp(-expected_cards),
        shots_1=1 - math.exp(-expected_shots),
        shots_2=1 - math.exp(-expected_shots) * (1 + expected_shots),
    )
