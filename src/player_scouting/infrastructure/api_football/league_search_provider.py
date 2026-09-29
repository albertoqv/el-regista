from __future__ import annotations

import httpx

from player_scouting.application.ports import LeagueSummary
from player_scouting.infrastructure.api_football.provider import (
    DEFAULT_BASE_URL,
    ApiFootballError,
)


class ApiFootballLeagueSearchProvider:
    def __init__(
        self,
        http_client: httpx.Client,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url

    def search_leagues(self, query: str) -> list[LeagueSummary]:
        response = self._http_client.get(
            f"{self._base_url}/leagues",
            params={"search": query},
            headers={"x-apisports-key": self._api_key},
        )
        response.raise_for_status()
        data = response.json()
        errors = data.get("errors")
        if errors:
            raise ApiFootballError(f"API-Football returned an error: {errors}")

        return [
            LeagueSummary(
                id=entry["league"]["id"],
                name=entry["league"]["name"],
                country=entry["country"]["name"],
            )
            for entry in data.get("response", [])
        ]
