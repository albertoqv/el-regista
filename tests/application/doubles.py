from __future__ import annotations

from datetime import date

from player_scouting.application.ports import PlayerCompetitionStats
from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics


class InMemoryPlayerRepository:
    def __init__(self) -> None:
        self._entries: dict[int, tuple[Player, Statistics]] = {}

    def add(self, player: Player, statistics: Statistics) -> None:
        self._entries[player.player_id] = (player, statistics)

    def get(self, player_id: int) -> tuple[Player, Statistics] | None:
        return self._entries.get(player_id)

    def list_all(self) -> list[tuple[Player, Statistics]]:
        return list(self._entries.values())

    def save(self, player: Player, statistics: Statistics) -> None:
        self.add(player, statistics)


class FakeCompetitionStatisticsProvider:
    def __init__(self, stats: list[PlayerCompetitionStats]) -> None:
        self._stats = stats

    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> list[PlayerCompetitionStats]:
        return self._stats


class FakeBirthDateProvider:
    def __init__(self, dates_by_name: dict[str, date | None]) -> None:
        self._dates_by_name = dates_by_name

    def find(self, name: str, nationality: str | None = None) -> date | None:
        return self._dates_by_name.get(name)
