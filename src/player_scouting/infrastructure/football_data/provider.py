from __future__ import annotations

import csv
import io
import time
from collections.abc import Callable
from typing import Protocol

from player_scouting.application.ports import MatchStats
from player_scouting.infrastructure.football_data.mapper import LEAGUES, to_match_stats

PAUSE_BETWEEN_FILES_SECONDS = 1.0


class CsvClient(Protocol):
    def season_csv(self, league_code: str, start_year: int) -> str: ...

    def upcoming_csv(self) -> str: ...


def _rows(text: str) -> list[dict[str, str]]:
    return [
        row
        for row in csv.DictReader(io.StringIO(text.lstrip("﻿")))
        if row.get("HomeTeam") and row.get("Date")
    ]


def _season_of(played_on) -> str:
    return str(played_on.year if played_on.month >= 7 else played_on.year - 1)


class FootballDataProvider:
    def __init__(
        self, client: CsvClient, pause: Callable[[float], None] = time.sleep
    ) -> None:
        self._client = client
        self._pause = pause

    def season(self, start_year: int) -> list[MatchStats]:
        matches: list[MatchStats] = []
        for index, (code, competition) in enumerate(LEAGUES.items()):
            if index:
                self._pause(PAUSE_BETWEEN_FILES_SECONDS)
            for row in _rows(self._client.season_csv(code, start_year)):
                matches.append(to_match_stats(row, competition, str(start_year)))
        return matches

    def upcoming(self) -> list[MatchStats]:
        matches = []
        for row in _rows(self._client.upcoming_csv()):
            competition = LEAGUES.get(row.get("Div", ""))
            if competition is None:
                continue
            match = to_match_stats(row, competition, "")
            matches.append(
                MatchStats(
                    **{
                        **match.__dict__,
                        "season_label": _season_of(match.played_on),
                    }
                )
            )
        return matches
