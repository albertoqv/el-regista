from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from player_scouting.application.ports import AdvancedSeasonRow
from player_scouting.infrastructure.understat.mapper import to_advanced_row

# Understat league codes → the competition names FBref ingestion already uses.
LEAGUES = {
    "EPL": "Premier League",
    "La_liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A": "Serie A",
    "Ligue_1": "Ligue 1",
}
PAUSE_BETWEEN_LEAGUES_SECONDS = 1.0


class LeaguePlayersClient(Protocol):
    def get_league_players(self, league: str, season: int) -> list[dict]: ...


class UnderstatSeasonProvider:
    def __init__(
        self,
        client: LeaguePlayersClient,
        pause: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._pause = pause

    def get_season(self, start_year: int) -> list[AdvancedSeasonRow]:
        rows: list[AdvancedSeasonRow] = []
        for index, (league, competition) in enumerate(LEAGUES.items()):
            if index:
                self._pause(PAUSE_BETWEEN_LEAGUES_SECONDS)
            for raw in self._client.get_league_players(league, start_year):
                rows.append(to_advanced_row(raw, competition))
        return rows
