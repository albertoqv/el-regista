"""A player's numbers in one competition of one season: league, Champions League,
cup, super cup or a national team tournament."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CompetitionKind = Literal["league", "continental", "cup", "supercup", "national"]

# The order a season's lines are shown in.
KIND_ORDER: dict[CompetitionKind, int] = {
    "league": 0,
    "continental": 1,
    "cup": 2,
    "supercup": 3,
    "national": 4,
}


@dataclass(frozen=True)
class CompetitionLine:
    competition: str
    kind: CompetitionKind
    # Clubs: the year the season starts ("2025" = 25/26). National teams: the year of
    # the tournament ("2026" = World Cup 2026).
    season_label: str
    team: str | None
    appearances: int
    goals: int
    assists: int
    minutes_played: int
    yellow_cards: int
    red_cards: int


def sorted_lines(lines: list[CompetitionLine]) -> list[CompetitionLine]:
    """Newest season first; inside a season, league, Europe, cups, super cups."""
    return sorted(
        lines,
        key=lambda line: (
            -int(line.season_label),
            KIND_ORDER[line.kind],
            -line.minutes_played,
        ),
    )
