from __future__ import annotations

from dataclasses import dataclass, fields, replace

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
    "minutes_played",
)

_NON_NEGATIVE_FLOAT_FIELDS = (
    "expected_goals",
    "expected_assists",
    "xg_chain",
    "xg_buildup",
)


def _field_label(field_name: str) -> str:
    return field_name.replace("_", " ").capitalize()


def _validate_non_negative_ints(obj: object, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(obj, field_name)
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidStatisticsError(f"{_field_label(field_name)} must be an integer")
        if value < 0:
            raise InvalidStatisticsError(
                f"{_field_label(field_name)} must be equal to or greater than 0"
            )


def _validate_non_negative_numbers(obj: object, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(obj, field_name)
        if not isinstance(value, int | float) or isinstance(value, bool):
            raise InvalidStatisticsError(f"{_field_label(field_name)} must be a number")
        if value < 0:
            raise InvalidStatisticsError(
                f"{_field_label(field_name)} must be equal to or greater than 0"
            )


@dataclass(frozen=True)
class AdvancedStatistics:
    expected_goals: float
    expected_assists: float
    key_passes: int
    xg_chain: float
    xg_buildup: float

    def __post_init__(self) -> None:
        _validate_non_negative_ints(self, ("key_passes",))
        _validate_non_negative_numbers(
            self, ("expected_goals", "expected_assists", "xg_chain", "xg_buildup")
        )


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
    minutes_played: int = 0
    expected_assists: float = 0.0
    xg_chain: float = 0.0
    xg_buildup: float = 0.0

    def __post_init__(self) -> None:
        _validate_non_negative_ints(self, _NON_NEGATIVE_INT_FIELDS)
        _validate_non_negative_numbers(self, _NON_NEGATIVE_FLOAT_FIELDS)

    def __add__(self, other: object) -> Statistics:
        if not isinstance(other, Statistics):
            return NotImplemented
        values = {
            field.name: getattr(self, field.name) + getattr(other, field.name)
            for field in fields(self)
        }
        return Statistics(**values)

    def with_advanced(self, advanced: AdvancedStatistics) -> Statistics:
        return replace(
            self,
            expected_goals=advanced.expected_goals,
            key_passes=advanced.key_passes,
            expected_assists=advanced.expected_assists,
            xg_chain=advanced.xg_chain,
            xg_buildup=advanced.xg_buildup,
        )
