from __future__ import annotations

import httpx

DEFAULT_BASE_URL = "https://www.transfermarkt.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class TransfermarktClient:
    def __init__(
        self,
        http_client: httpx.Client,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._base_url = base_url

    def search_player(self, name: str) -> str:
        response = self._get(
            f"{self._base_url}/schnellsuche/ergebnis/schnellsuche",
            params={"query": name},
        )
        return response.text

    def get_profile(self, profile_path: str) -> str:
        response = self._get(f"{self._base_url}{profile_path}")
        return response.text

    def get_market_value_graph(self, player_id: int) -> dict:
        response = self._get(
            f"{self._base_url}/ceapi/marketValueDevelopment/graph/{player_id}"
        )
        return response.json()

    def _get(self, url: str, params: dict | None = None) -> httpx.Response:
        response = self._http_client.get(
            url, params=params, headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()
        return response
