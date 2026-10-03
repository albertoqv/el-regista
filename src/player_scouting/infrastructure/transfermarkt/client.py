from __future__ import annotations

import httpx

from player_scouting.application.ports import EnrichmentUnavailableError

DEFAULT_BASE_URL = "https://www.transfermarkt.com"
NO_RESULTS = "/schnellsuche/keinergebnis/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _refuse_challenge(response: httpx.Response) -> None:
    """Transfermarkt's AWS WAF answers datacenter IPs with an empty 202 and a
    challenge header: that is a block, never an empty page (which would read as
    "player not found" and mark him as checked)."""
    if response.headers.get("x-amzn-waf-action") or response.status_code == 202:
        raise EnrichmentUnavailableError("Transfermarkt bot challenge (AWS WAF)")


class TransfermarktClient:
    def __init__(
        self,
        http_client: httpx.Client,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._base_url = base_url

    def search_player(self, name: str) -> str:
        response = self._http_client.get(
            f"{self._base_url}/schnellsuche/ergebnis/schnellsuche",
            params={"query": name},
            headers={"User-Agent": USER_AGENT},
        )
        _refuse_challenge(response)
        # No results: Transfermarkt redirects to a "keinergebnis" page.
        if response.is_redirect and NO_RESULTS in response.headers.get("Location", ""):
            return ""
        response.raise_for_status()
        return response.text

    def get_profile(self, profile_path: str) -> str:
        response = self._get(f"{self._base_url}{profile_path}")
        return response.text

    def get_market_value_graph(self, player_id: int) -> dict:
        response = self._get(
            f"{self._base_url}/ceapi/marketValueDevelopment/graph/{player_id}"
        )
        return response.json()

    def get_page(self, path: str) -> str:
        return self._get(f"{self._base_url}{path}").text

    def _get(self, url: str, params: dict | None = None) -> httpx.Response:
        response = self._http_client.get(
            url, params=params, headers={"User-Agent": USER_AGENT}
        )
        _refuse_challenge(response)
        response.raise_for_status()
        return response
