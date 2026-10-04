from __future__ import annotations

import re
from dataclasses import dataclass

_YEAR_PATTERN = re.compile(r"\d{4}")


@dataclass(frozen=True)
class Season:
    competition: str
    label: str

    @property
    def start_year(self) -> int | None:
        match = _YEAR_PATTERN.search(self.label)
        return int(match.group()) if match else None


# The leagues with full stats (FBref + Understat); the rest only have goals,
# assists, minutes and cards.
BIG_FIVE: tuple[str, ...] = (
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Serie A",
    "Ligue 1",
)
