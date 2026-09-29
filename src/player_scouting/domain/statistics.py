from __future__ import annotations

from dataclasses import dataclass, fields

from player_scouting.domain.exceptions import InvalidStatisticsError

_NON_NEGATIVE_INT_FIELDS = (
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "passes_completed",
    "passes_attempted",
    "key_passes",
    "dribbles_completed",
    "dribbles_attempted",
    "tackles_won",
    "interceptions",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "red_cards",
)


def _field_label(field_name: str) -> str:
    return field_name.replace("_", " ").capitalize()


@dataclass(frozen=True)
class Statistics:
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

    def __post_init__(self) -> None:
        for field_name in _NON_NEGATIVE_INT_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise InvalidStatisticsError(
                    f"{_field_label(field_name)} must be an integer"
                )
            if value < 0:
                raise InvalidStatisticsError(
                    f"{_field_label(field_name)} must be equal to or greater than 0"
                )

        if not isinstance(self.expected_goals, int | float) or isinstance(
            self.expected_goals, bool
        ):
            raise InvalidStatisticsError("Expected goals must be a number")
        if self.expected_goals < 0:
            raise InvalidStatisticsError(
                "Expected goals must be equal to or greater than 0"
            )

    def __add__(self, other: object) -> Statistics:
        if not isinstance(other, Statistics):
            return NotImplemented
        values = {
            field.name: getattr(self, field.name) + getattr(other, field.name)
            for field in fields(self)
        }
        return Statistics(**values)
