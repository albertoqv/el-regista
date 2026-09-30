from __future__ import annotations

import httpx

BASE_URL = "https://www.football-data.co.uk"


class FootballDataClient:
    """football-data.co.uk: free CSVs with match stats and bookmaker odds."""

    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def season_csv(self, league_code: str, start_year: int) -> str:
        season = f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"
        return self._get(f"{BASE_URL}/mmz4281/{season}/{league_code}.csv")

    def upcoming_csv(self) -> str:
        return self._get(f"{BASE_URL}/fixtures.csv")

    def _get(self, url: str) -> str:
        response = self._http_client.get(url, follow_redirects=True, timeout=60)
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        # Files are UTF-8 with BOM, some older ones latin-1.
        try:
            return response.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return response.content.decode("latin-1")
