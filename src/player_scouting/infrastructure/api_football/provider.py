from __future__ import annotations

from datetime import date

import httpx

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics

DEFAULT_BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballError(Exception):
    pass


class ApiFootballPlayerSeasonProvider:
    def __init__(
        self,
        http_client: httpx.Client,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        self._http_client = http_client
        self._api_key = api_key
        self._base_url = base_url

    def get_player_statistics(
        self, player_name: str, league_id: int, season_year: int
    ) -> PlayerSeasonResult | None:
        response = self._http_client.get(
            f"{self._base_url}/players",
            params={
                "league": league_id,
                "season": season_year,
                "search": player_name,
            },
            headers={"x-apisports-key": self._api_key},
        )
        response.raise_for_status()
        data = response.json()
        errors = data.get("errors")
        if errors:
            raise ApiFootballError(f"API-Football returned an error: {errors}")

        results = data.get("response", [])
        if not results:
            return None

        entry = results[0]
        stats_blocks = entry.get("statistics") or []
        if not stats_blocks:
            return None

        return self._to_result(entry["player"], stats_blocks[0], season_year)

    @staticmethod
    def _to_result(
        player_info: dict, stats_block: dict, season_year: int
    ) -> PlayerSeasonResult:
        games = stats_block.get("games") or {}
        shots = stats_block.get("shots") or {}
        goals = stats_block.get("goals") or {}
        passes = stats_block.get("passes") or {}
        tackles = stats_block.get("tackles") or {}
        dribbles = stats_block.get("dribbles") or {}
        fouls = stats_block.get("fouls") or {}
        cards = stats_block.get("cards") or {}
        league = stats_block.get("league") or {}

        passes_attempted = passes.get("total") or 0
        accuracy = passes.get("accuracy") or 0
        passes_completed = round(passes_attempted * accuracy / 100)

        statistics = Statistics(
            goals=goals.get("total") or 0,
            assists=goals.get("assists") or 0,
            shots=shots.get("total") or 0,
            shots_on_target=shots.get("on") or 0,
            passes_completed=passes_completed,
            passes_attempted=passes_attempted,
            key_passes=passes.get("key") or 0,
            dribbles_completed=dribbles.get("success") or 0,
            dribbles_attempted=dribbles.get("attempts") or 0,
            tackles_won=tackles.get("total") or 0,
            interceptions=tackles.get("interceptions") or 0,
            fouls_committed=fouls.get("committed") or 0,
            fouls_won=fouls.get("drawn") or 0,
            yellow_cards=cards.get("yellow") or 0,
            red_cards=(cards.get("red") or 0) + (cards.get("yellowred") or 0),
        )

        season = Season(
            league.get("name") or "Unknown",
            str(league.get("season") or season_year),
        )

        return PlayerSeasonResult(
            player_id=player_info["id"],
            name=player_info["name"],
            position=games.get("position"),
            date_of_birth=date.fromisoformat(player_info["birth"]["date"]),
            season=season,
            statistics=statistics,
            photo_url=player_info.get("photo"),
        )
