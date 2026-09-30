from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol

from player_scouting.application.ports import MatchRef
from player_scouting.domain.shots import Shot
from player_scouting.infrastructure.understat.mapper import to_match_ref, to_shot
from player_scouting.infrastructure.understat.provider import (
    LEAGUES,
    PAUSE_BETWEEN_LEAGUES_SECONDS,
)


class MatchesClient(Protocol):
    def get_league_matches(self, league: str, season: int) -> list[dict]: ...

    def get_match_shots(self, match_id: int) -> dict: ...


class UnderstatShotProvider:
    def __init__(
        self,
        client: MatchesClient,
        pause: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._pause = pause

    def list_played_matches(self, start_year: int) -> list[MatchRef]:
        matches: list[MatchRef] = []
        for index, (league, competition) in enumerate(LEAGUES.items()):
            if index:
                self._pause(PAUSE_BETWEEN_LEAGUES_SECONDS)
            matches.extend(
                to_match_ref(raw, competition, str(start_year))
                for raw in self._client.get_league_matches(league, start_year)
                if raw.get("isResult")
            )
        return matches

    def get_match_shots(self, match: MatchRef) -> list[Shot]:
        sides = self._client.get_match_shots(match.match_id)
        return [to_shot(raw) for side in ("h", "a") for raw in sides.get(side, [])]
