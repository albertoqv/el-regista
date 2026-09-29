from __future__ import annotations

import httpx

from player_scouting.application.ports import (
    LeaguePageUnavailableError,
    LeaguePlayersPage,
)
from player_scouting.infrastructure.api_football.mapper import (
    to_player_season_result,
)
from player_scouting.infrastructure.api_football.provider import (
    DEFAULT_BASE_URL,
    ApiFootballError,
)


class ApiFootballLeaguePlayersProvider:
    def __init__(
        self,
        http_client: httpx.Client,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url

    def get_players_page(
        self, league_id: int, season_year: int, page: int
    ) -> LeaguePlayersPage:
        response = self._http_client.get(
            f"{self._base_url}/players",
            params={"league": league_id, "season": season_year, "page": page},
            headers={"x-apisports-key": self._api_key},
        )
        response.raise_for_status()
        data = response.json()
        errors = data.get("errors")
        if errors:
            if isinstance(errors, dict) and "plan" in errors:
                raise LeaguePageUnavailableError(
                    f"API-Football plan limit reached for page {page}: {errors}"
                )
            raise ApiFootballError(f"API-Football returned an error: {errors}")

        players = []
        for entry in data.get("response", []):
            stats_blocks = entry.get("statistics") or []
            if not stats_blocks:
                continue
            try:
                players.append(
                    to_player_season_result(
                        entry["player"], stats_blocks[0], season_year
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

        paging = data.get("paging") or {}
        return LeaguePlayersPage(
            players=players,
            current_page=paging.get("current", page),
            total_pages=paging.get("total", page),
        )
