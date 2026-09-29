from __future__ import annotations

import httpx

DEFAULT_BASE_URL = "https://understat.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class UnderstatClient:
    def __init__(
        self, http_client: httpx.Client, base_url: str = DEFAULT_BASE_URL
    ) -> None:
        self._http_client = http_client
        self._base_url = base_url

    def get_league_players(self, league: str, season: int) -> list[dict]:
        response = self._http_client.get(
            f"{self._base_url}/getLeagueData/{league}/{season}",
            headers={
                "User-Agent": USER_AGENT,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self._base_url}/league/{league}/{season}",
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("players", [])
