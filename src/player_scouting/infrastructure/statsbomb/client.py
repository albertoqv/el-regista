from __future__ import annotations

import httpx

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"


class StatsBombClient:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client or httpx.Client()
        self._base_url = base_url.rstrip("/")

    def get_matches(self, competition_id: int, season_id: int) -> list[dict]:
        return self._get(f"matches/{competition_id}/{season_id}.json")

    def get_lineups(self, match_id: int) -> list[dict]:
        return self._get(f"lineups/{match_id}.json")

    def get_events(self, match_id: int) -> list[dict]:
        return self._get(f"events/{match_id}.json")

    def _get(self, path: str) -> list[dict]:
        response = self._http_client.get(f"{self._base_url}/{path}")
        response.raise_for_status()
        return response.json()
