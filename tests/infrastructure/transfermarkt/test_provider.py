from datetime import date

from player_scouting.infrastructure.transfermarkt.provider import (
    TransfermarktMarketValueProvider,
)

SEARCH_RESULTS_HTML = """
<a href="/jude-bellingham/profil/spieler/581678">Jude Bellingham</a>
"""

PROFILE_HTML = """
<span class="info-table__content info-table__content--regular">Foot:</span>
<span class="info-table__content info-table__content--bold">right</span>
"""

MARKET_VALUE_GRAPH_JSON = {
    "list": [
        {
            "x": 1571270400000,
            "y": 2500000,
            "datum_mw": "17/10/2019",
            "verein": "Birmingham City",
            "age": "16",
        },
        {
            "x": 1735689600000,
            "y": 160000000,
            "datum_mw": "01/01/2025",
            "verein": "Real Madrid",
            "age": "21",
        },
    ]
}


class FakeTransfermarktClient:
    def __init__(
        self,
        search_html: str = SEARCH_RESULTS_HTML,
        profile_html: str = PROFILE_HTML,
        market_value_graph: dict | None = None,
    ) -> None:
        self._search_html = search_html
        self._profile_html = profile_html
        self._market_value_graph = market_value_graph or MARKET_VALUE_GRAPH_JSON
        self.requested_profile_paths: list[str] = []
        self.requested_player_ids: list[int] = []

    def search_player(self, name: str) -> str:
        return self._search_html

    def get_profile(self, profile_path: str) -> str:
        self.requested_profile_paths.append(profile_path)
        return self._profile_html

    def get_market_value_graph(self, player_id: int) -> dict:
        self.requested_player_ids.append(player_id)
        return self._market_value_graph


def test_builds_a_market_value_history_result_for_a_found_player():
    client = FakeTransfermarktClient()
    provider = TransfermarktMarketValueProvider(client)

    result = provider.get_market_value_history("Jude Bellingham")

    assert result is not None
    assert result.preferred_foot == "right"
    assert len(result.points) == 2
    assert result.points[0].as_of == date(2019, 10, 17)
    assert result.points[-1].amount_eur == 160_000_000
    assert client.requested_profile_paths == ["/jude-bellingham/profil/spieler/581678"]
    assert client.requested_player_ids == [581678]


def test_returns_none_when_no_search_results_are_found():
    client = FakeTransfermarktClient(search_html="<html>no results</html>")
    provider = TransfermarktMarketValueProvider(client)

    result = provider.get_market_value_history("Nobody")

    assert result is None
