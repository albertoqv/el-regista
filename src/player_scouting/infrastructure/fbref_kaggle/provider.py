from __future__ import annotations

import csv
import io
from typing import Protocol

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.infrastructure.fbref_kaggle.mapper import rows_to_results


class SeasonCsvClient(Protocol):
    def download_season_csv(self, start_year: int) -> str: ...


class FbrefKaggleSeasonProvider:
    def __init__(self, client: SeasonCsvClient) -> None:
        self._client = client

    def get_season(self, start_year: int) -> list[PlayerSeasonResult]:
        text = self._client.download_season_csv(start_year)
        return rows_to_results(csv.DictReader(io.StringIO(text)), start_year)
