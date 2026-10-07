"""A player's output across his career, season by season, placed at his age.

Club seasons only (league, Europe, cups, super cups): national teams are another
calendar. The output is goals plus assists per 90 minutes, the one rate every
competition has.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from player_scouting.domain.competitions import CompetitionLine

# Below this, a season says nothing about his level (a cameo, an injury year).
MINIMUM_MINUTES = 270


@dataclass(frozen=True)
class CareerPoint:
    season_label: str
    age: int
    appearances: int
    goals: int
    assists: int
    minutes_played: int
    per90: float


@dataclass(frozen=True)
class AgePoint:
    """The level of the players of one position at one age (benchmark)."""

    age: int
    per90: float
    players: int


def career_by_age(
    lines: list[CompetitionLine], birth_year: int | None
) -> list[CareerPoint]:
    if birth_year is None:
        return []
    seasons: dict[str, list[CompetitionLine]] = defaultdict(list)
    for line in lines:
        if line.kind != "national":
            seasons[line.season_label].append(line)
    points = []
    for label, group in seasons.items():
        minutes = sum(line.minutes_played for line in group)
        if minutes < MINIMUM_MINUTES:
            continue
        goals = sum(line.goals for line in group)
        assists = sum(line.assists for line in group)
        points.append(
            CareerPoint(
                season_label=label,
                # The age he turns in the year the season starts.
                age=int(label) - birth_year,
                appearances=sum(line.appearances for line in group),
                goals=goals,
                assists=assists,
                minutes_played=minutes,
                per90=round((goals + assists) * 90 / minutes, 3),
            )
        )
    return sorted(points, key=lambda point: point.age)
