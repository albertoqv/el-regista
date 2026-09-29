from __future__ import annotations

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
