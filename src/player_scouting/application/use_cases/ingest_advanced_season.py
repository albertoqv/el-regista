from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.player_matching import MatchCandidate, match_players
from player_scouting.application.ports import (
    AdvancedSeasonProvider,
    AdvancedSeasonRow,
    PlayerRepository,
)
from player_scouting.application.team_names import learn_team_aliases
from player_scouting.domain.season import Season


@dataclass
class IngestAdvancedSeasonUseCase:
    provider: AdvancedSeasonProvider
    repository: PlayerRepository

    def execute(self, start_year: int) -> IngestionResult:
        rows_by_competition: dict[str, list[AdvancedSeasonRow]] = defaultdict(list)
        for row in self.provider.get_season(start_year):
            rows_by_competition[row.competition].append(row)

        ingested = 0
        skipped: list[SkippedPlayer] = []
        for competition, rows in rows_by_competition.items():
            season = Season(competition, str(start_year))
            entries = self.repository.list_season_entries(season)
            teams = {entry.player.player_id: entry.team for entry in entries}
            candidates = [
                MatchCandidate(
                    player_id=entry.player.player_id,
                    name=entry.player.name,
                    team=entry.team,
                    minutes=entry.statistics.minutes_played,
                    goals=entry.statistics.goals,
                )
                for entry in entries
            ]
            matches = match_players([row.player for row in rows], candidates)
            for row in rows:
                player_id = matches.get(row.player.external_id)
                if player_id is None:
                    skipped.append(
                        SkippedPlayer(
                            row.player.external_id,
                            row.player.name,
                            f"no match in {competition} {start_year}",
                        )
                    )
                    continue
                self.repository.save_season_advanced(player_id, season, row.advanced)
                self.repository.set_understat_id(player_id, row.player.external_id)
                ingested += 1
            aliases = learn_team_aliases(
                (teams.get(matches[row.player.external_id]), row.player.teams)
                for row in rows
                if row.player.external_id in matches
            )
            for fbref_team, understat_team in aliases.items():
                self.repository.rename_season_team(season, fbref_team, understat_team)

        return IngestionResult(ingested=ingested, skipped=skipped)
