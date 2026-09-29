from __future__ import annotations

from player_scouting.application.ports import (
    CompetitionStatisticsResult,
    PlayerCompetitionStats,
)
from player_scouting.domain.season import Season
from player_scouting.infrastructure.statsbomb.client import StatsBombClient
from player_scouting.infrastructure.statsbomb.mapper import (
    PlayerMatchStats,
    extract_lineup_players,
    extract_player_statistics,
    merge_statistics,
)


class StatsBombCompetitionStatisticsProvider:
    def __init__(self, client: StatsBombClient) -> None:
        self._client = client

    def get_statistics(
        self, competition_id: int, season_id: int
    ) -> CompetitionStatisticsResult:
        matches = self._client.get_matches(competition_id, season_id)

        aggregated: dict[int, PlayerMatchStats] = {}
        nationalities: dict[int, str] = {}
        for match in matches:
            match_id = match["match_id"]
            lineups = self._client.get_lineups(match_id)
            merge_statistics(aggregated, extract_lineup_players(lineups))
            merge_statistics(
                aggregated, extract_player_statistics(self._client.get_events(match_id))
            )
            nationalities.update(self._extract_nationalities(lineups))

        players = [
            PlayerCompetitionStats(
                player_id=stats.player_id,
                name=stats.name,
                position=stats.position,
                nationality=nationalities.get(stats.player_id),
                goals=stats.goals,
                assists=stats.assists,
                shots=stats.shots,
                shots_on_target=stats.shots_on_target,
                expected_goals=stats.expected_goals,
                passes_completed=stats.passes_completed,
                passes_attempted=stats.passes_attempted,
                key_passes=stats.key_passes,
                dribbles_completed=stats.dribbles_completed,
                dribbles_attempted=stats.dribbles_attempted,
                tackles_won=stats.tackles_won,
                interceptions=stats.interceptions,
                fouls_committed=stats.fouls_committed,
                fouls_won=stats.fouls_won,
                yellow_cards=stats.yellow_cards,
                red_cards=stats.red_cards,
            )
            for stats in aggregated.values()
        ]
        return CompetitionStatisticsResult(
            season=self._season_from(matches, competition_id, season_id),
            players=players,
        )

    @staticmethod
    def _season_from(
        matches: list[dict], competition_id: int, season_id: int
    ) -> Season:
        if not matches:
            return Season(str(competition_id), str(season_id))
        first_match = matches[0]
        competition_name = first_match["competition"]["competition_name"]
        season_name = first_match["season"]["season_name"]
        return Season(competition_name, season_name)

    def _extract_nationalities(self, lineups: list[dict]) -> dict[int, str]:
        nationalities: dict[int, str] = {}
        for team_lineup in lineups:
            for player in team_lineup.get("lineup", []):
                country = player.get("country") or {}
                nationality = country.get("name")
                if nationality:
                    nationalities[player["player_id"]] = nationality
        return nationalities
