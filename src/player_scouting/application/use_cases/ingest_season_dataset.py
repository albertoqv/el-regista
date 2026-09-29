from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.ports import (
    PlayerRepository,
    PlayerSeasonResult,
    SeasonDatasetProvider,
)
from player_scouting.domain.entities import Player

UNKNOWN_POSITION = "Unknown"


@dataclass
class IngestSeasonDatasetUseCase:
    provider: SeasonDatasetProvider
    repository: PlayerRepository

    def execute(self, start_year: int) -> IngestionResult:
        results = self.provider.get_season(start_year)
        for result in results:
            self.repository.save_player(self._merge_with_existing(result))
            self.repository.save_season_statistics(
                result.player_id, result.season, result.statistics
            )
        return IngestionResult(ingested=len(results), skipped=[])

    def _merge_with_existing(self, result: PlayerSeasonResult) -> Player:
        existing = self.repository.get_player(result.player_id)
        return Player(
            result.player_id,
            result.name,
            result.position or UNKNOWN_POSITION,
            result.date_of_birth,
            photo_url=result.photo_url or (existing.photo_url if existing else None),
            preferred_foot=existing.preferred_foot if existing else None,
            birth_year=result.birth_year,
        )
