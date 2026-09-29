from __future__ import annotations

from player_scouting.application.ports import PlayerCompetitionStats
from player_scouting.infrastructure.statsbomb.client import StatsBombClient
from player_scouting.infrastructure.statsbomb.mapper import (
    PlayerMatchStats,
    extract_player_statistics,
    merge_statistics,
)


class StatsBombCompetitionStatisticsProvider:
    def __init__(self, client: StatsBombClient) -> None:
        self._client = client

    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> list[PlayerCompetitionStats]:
        matches = self._client.get_matches(competition_id, season_id)

        aggregated: dict[int, PlayerMatchStats] = {}
        nationalities: dict[int, str] = {}
        for match in matches:
            match_id = match["match_id"]
            match_stats = extract_player_statistics(self._client.get_events(match_id))
            merge_statistics(aggregated, match_stats)
            nationalities.update(self._extract_nationalities(match_id))

        return [
            PlayerCompetitionStats(
                player_id=stats.player_id,
                name=stats.name,
                position=stats.position,
                nationality=nationalities.get(stats.player_id),
                goals=stats.goals,
                assists=stats.assists,
            )
            for stats in aggregated.values()
        ]

    def _extract_nationalities(self, match_id: int) -> dict[int, str]:
        nationalities: dict[int, str] = {}
        for team_lineup in self._client.get_lineups(match_id):
            for player in team_lineup.get("lineup", []):
                country = player.get("country") or {}
                nationality = country.get("name")
                if nationality:
                    nationalities[player["player_id"]] = nationality
        return nationalities
