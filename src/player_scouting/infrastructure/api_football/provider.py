from __future__ import annotations

import httpx

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.infrastructure.api_football.mapper import (
    to_player_season_result,
)

DEFAULT_BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballError(Exception):
    pass


class ApiFootballPlayerSeasonProvider:
    def __init__(
        self,
        http_client: httpx.Client,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url

    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None:
        response = self._http_client.get(
            f"{self._base_url}/players",
            params={
                "league": league_id,
                "season": season_year,
                "search": player_name,
            },
            headers={"x-apisports-key": self._api_key},
        )
        response.raise_for_status()
        data = response.json()
        errors = data.get("errors")
        if errors:
            raise ApiFootballError(f"API-Football returned an error: {errors}")

        results = data.get("response", [])
        if not results:
            return None

        entry = results[0]
        stats_blocks = entry.get("statistics") or []
        if not stats_blocks:
            return None

        return to_player_season_result(entry["player"], stats_blocks[0], season_year)
