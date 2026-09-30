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
        return self._league_data(league, season).get("players", [])

    def get_league_data(self, league: str, season: int) -> dict:
        return self._league_data(league, season)

    def get_league_matches(self, league: str, season: int) -> list[dict]:
        return self._league_data(league, season).get("dates", [])

    def get_match_rosters(self, match_id: int) -> dict:
        data = self._get(
            f"/getMatchData/{match_id}", referer=f"{self._base_url}/match/{match_id}"
        )
        return data.get("rosters", {"h": {}, "a": {}})

    def get_match_shots(self, match_id: int) -> dict:
        data = self._get(
            f"/getMatchData/{match_id}", referer=f"{self._base_url}/match/{match_id}"
        )
        return data.get("shots", {"h": [], "a": []})

    def _league_data(self, league: str, season: int) -> dict:
        return self._get(
            f"/getLeagueData/{league}/{season}",
            referer=f"{self._base_url}/league/{league}/{season}",
        )

    def _get(self, path: str, referer: str) -> dict:
        response = self._http_client.get(
            f"{self._base_url}{path}",
            headers={
                "User-Agent": USER_AGENT,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": referer,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
