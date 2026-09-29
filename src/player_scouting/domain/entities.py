from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from player_scouting.domain.exceptions import InvalidPlayerError


@dataclass(eq=False)
class Player:
    player_id: int
    name: str
    position: str
    date_of_birth: date
    photo_url: str | None = None
    preferred_foot: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.player_id, int) or isinstance(self.player_id, bool):
            raise InvalidPlayerError("The player_id must be an integer")
        if self.player_id <= 0:
            raise InvalidPlayerError("The player_id must be a value greater than 0")
        if self.date_of_birth > date.today():
            raise InvalidPlayerError("The date cannot be in the future")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.player_id == other.player_id

    def __hash__(self) -> int:
        return hash(self.player_id)
