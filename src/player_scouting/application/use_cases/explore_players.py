from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, fields
from datetime import date
from typing import Literal

from player_scouting.application.ports import PlayerRepository, SeasonRecord
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.percentiles import per_90
from player_scouting.domain.statistics import Statistics

ExploreSort = Literal[
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "expected_goals",
    "expected_assists",
    "key_passes",
    "xg_chain",
    "xg_buildup",
    "passes_completed",
    "dribbles_completed",
    "tackles_won",
    "interceptions",
    "fouls_won",
    "minutes_played",
    "market_value",
    "age",
]
_STAT_FIELDS = {f.name for f in fields(Statistics)}


@dataclass(frozen=True)
class ExploreFilters:
    season_label: str
    competition: str | None = None
    position: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    max_value: int | None = None
    min_minutes: int = 0
    sort: ExploreSort = "goals"
    per_90: bool = False
    ascending: bool = False
    limit: int = 50


@dataclass(frozen=True)
class ExploreRow:
    record: SeasonRecord
    market_value: MarketValuePoint | None
    age: int | None
    sort_value: float


def age_on(player: Player, today: date) -> int | None:
    if player.date_of_birth is not None:
        born = player.date_of_birth
        return (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
    if player.birth_year is not None:
        return today.year - player.birth_year
    return None


@dataclass
class ExplorePlayersUseCase:
    repository: PlayerRepository
    today: Callable[[], date] = field(default=date.today)

    def execute(self, filters: ExploreFilters) -> list[ExploreRow]:
        values = self.repository.latest_market_values()
        today = self.today()
        rows = []
        for record in self.repository.list_season_records([filters.season_label]):
            player, statistics = record.player, record.statistics
            if filters.competition and record.season.competition != filters.competition:
                continue
            if filters.position and player.position != filters.position:
                continue
            if statistics.minutes_played < filters.min_minutes:
                continue
            age = age_on(player, today)
            if filters.min_age is not None and (age is None or age < filters.min_age):
                continue
            if filters.max_age is not None and (age is None or age > filters.max_age):
                continue
            value = values.get(player.player_id)
            if filters.max_value is not None and (
                value is None or value.amount_eur > filters.max_value
            ):
                continue
            sort_value = self._sort_value(filters, statistics, value, age)
            if sort_value is None:
                continue
            rows.append(ExploreRow(record, value, age, sort_value))
        rows.sort(
            key=lambda row: (
                row.sort_value if filters.ascending else -row.sort_value,
                row.record.player.name,
            )
        )
        return rows[: filters.limit]

    @staticmethod
    def _sort_value(
        filters: ExploreFilters,
        statistics: Statistics,
        value: MarketValuePoint | None,
        age: int | None,
    ) -> float | None:
        if filters.sort == "market_value":
            return float(value.amount_eur) if value else None
        if filters.sort == "age":
            return float(age) if age is not None else None
        if filters.sort not in _STAT_FIELDS:
            return None
        if filters.per_90 and filters.sort != "minutes_played":
            return per_90(statistics, filters.sort)
        return float(getattr(statistics, filters.sort))
