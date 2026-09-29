from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.ports import (
    PlayerRepository,
    PlayerSeasonStatisticsProvider,
)
from player_scouting.domain.entities import Player

UNKNOWN_POSITION = "Unknown"


@dataclass
class IngestPlayerSeasonUseCase:
    provider: PlayerSeasonStatisticsProvider
    repository: PlayerRepository

    def execute(
        self, player_name: str, league_id: int, season_year: int
    ) -> IngestionResult:
        result = self.provider.get_player_statistics(
            player_name, league_id, season_year
        )
        if result is None:
            return IngestionResult(
                ingested=0,
                skipped=[SkippedPlayer(0, player_name, "player not found")],
            )

        player = Player(
            result.player_id,
            result.name,
            result.position or UNKNOWN_POSITION,
            result.date_of_birth,
            photo_url=result.photo_url,
        )
        self.repository.save_player(player)
        self.repository.save_season_statistics(
            player.player_id, result.season, result.statistics
        )
        return IngestionResult(ingested=1, skipped=[])
