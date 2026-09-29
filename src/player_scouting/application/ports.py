from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics


class PlayerRepository(Protocol):
    def get(self, player_id: int) -> tuple[Player, Statistics] | None: ...

    def list_all(self) -> list[tuple[Player, Statistics]]: ...

    def save(self, player: Player, statistics: Statistics) -> None: ...


class BirthDateProvider(Protocol):
    def find(self, name: str, nationality: str | None = None) -> date | None: ...


@dataclass
class PlayerCompetitionStats:
    player_id: int
    name: str
    position: str | None
    nationality: str | None
    goals: int
    assists: int
    shots: int = 0
    shots_on_target: int = 0
    expected_goals: float = 0.0
    passes_completed: int = 0
    passes_attempted: int = 0
    key_passes: int = 0
    dribbles_completed: int = 0
    dribbles_attempted: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    fouls_committed: int = 0
    fouls_won: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class CompetitionStatisticsProvider(Protocol):
    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> list[PlayerCompetitionStats]: ...
