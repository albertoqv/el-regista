from __future__ import annotations

from datetime import date

from player_scouting.application.ports import (
    CompetitionStatisticsResult,
    MarketValueHistoryResult,
    PlayerSeasonResult,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics


class InMemoryPlayerRepository:
    def __init__(self) -> None:
        self._players: dict[int, Player] = {}
        self._season_statistics: dict[tuple[int, Season], Statistics] = {}
        self._market_value_history: dict[int, list[MarketValuePoint]] = {}

    def add(self, player: Player, season: Season, statistics: Statistics) -> None:
        self.save_player(player)
        self.save_season_statistics(player.player_id, season, statistics)

    def get_player(self, player_id: int) -> Player | None:
        return self._players.get(player_id)

    def list_players(self) -> list[Player]:
        return list(self._players.values())

    def save_player(self, player: Player) -> None:
        self._players[player.player_id] = player

    def save_season_statistics(
        self, player_id: int, season: Season, statistics: Statistics
    ) -> None:
        self._season_statistics[(player_id, season)] = statistics

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None:
        return self._season_statistics.get((player_id, season))

    def list_seasons_for_player(self, player_id: int) -> list[Season]:
        return [season for (pid, season) in self._season_statistics if pid == player_id]

    def get_career_statistics(self, player_id: int) -> Statistics:
        stats = [
            statistics
            for (pid, _), statistics in self._season_statistics.items()
            if pid == player_id
        ]
        return sum(stats, Statistics(0, 0))

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]:
        entries = []
        for (player_id, season), statistics in self._season_statistics.items():
            player = self._players.get(player_id)
            if player is not None:
                entries.append((player, season, statistics))
        return entries

    def save_market_value_history(
        self, player_id: int, points: list[MarketValuePoint]
    ) -> None:
        self._market_value_history[player_id] = list(points)

    def list_market_value_history(self, player_id: int) -> list[MarketValuePoint]:
        return self._market_value_history.get(player_id, [])


class FakeCompetitionStatisticsProvider:
    def __init__(self, result: CompetitionStatisticsResult) -> None:
        self._result = result

    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> CompetitionStatisticsResult:
        return self._result


class FakeBirthDateProvider:
    def __init__(self, dates_by_name: dict[str, date | None]) -> None:
        self._dates_by_name = dates_by_name

    def find(self, name: str, nationality: str | None = None) -> date | None:
        return self._dates_by_name.get(name)


class FakePlayerSeasonStatisticsProvider:
    def __init__(self, result: PlayerSeasonResult | None) -> None:
        self._result = result

    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None:
        return self._result


class FakeMarketValueProvider:
    def __init__(self, result: MarketValueHistoryResult | None) -> None:
        self._result = result

    def get_market_value_history(
        self, player_name: str
    ) -> MarketValueHistoryResult | None:
        return self._result
