from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from player_scouting.application.ports import Fixture, TeamMatch
from player_scouting.infrastructure.understat.mapper import to_fixture, to_team_matches
from player_scouting.infrastructure.understat.provider import (
    LEAGUES,
    PAUSE_BETWEEN_LEAGUES_SECONDS,
)


class LeagueDataClient(Protocol):
    def get_league_data(self, league: str, season: int) -> dict: ...


class UnderstatTeamProvider:
    """Calendar (played and upcoming) and per-team match metrics, 5 leagues."""

    def __init__(
        self,
        client: LeagueDataClient,
        pause: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._pause = pause

    def get_team_season(self, start_year: int) -> tuple[list[Fixture], list[TeamMatch]]:
        fixtures: list[Fixture] = []
        matches: list[TeamMatch] = []
        label = str(start_year)
        for index, (league, competition) in enumerate(LEAGUES.items()):
            if index:
                self._pause(PAUSE_BETWEEN_LEAGUES_SECONDS)
            data = self._client.get_league_data(league, start_year)
            fixtures.extend(
                to_fixture(raw, competition, label) for raw in data.get("dates", [])
            )
            matches.extend(to_team_matches(data, competition, label))
        return fixtures, matches
