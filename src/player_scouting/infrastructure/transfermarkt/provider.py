from __future__ import annotations

import re

from player_scouting.application.ports import MarketValueHistoryResult
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.mapper import (
    extract_preferred_foot,
    extract_profile_path,
    to_market_value_points,
)

PLAYER_ID_PATTERN = re.compile(r"/profil/spieler/(\d+)$")


class TransfermarktMarketValueProvider:
    def __init__(self, client: TransfermarktClient) -> None:
        self._client = client

    def get_market_value_history(
        self, player_name: str
    ) -> MarketValueHistoryResult | None:
        search_html = self._client.search_player(player_name)
        profile_path = extract_profile_path(search_html)
        if profile_path is None:
            return None

        match = PLAYER_ID_PATTERN.search(profile_path)
        if match is None:
            return None
        player_id = int(match.group(1))

        profile_html = self._client.get_profile(profile_path)
        preferred_foot = extract_preferred_foot(profile_html)

        graph = self._client.get_market_value_graph(player_id)
        points = to_market_value_points(graph.get("list", []))

        return MarketValueHistoryResult(preferred_foot=preferred_foot, points=points)
