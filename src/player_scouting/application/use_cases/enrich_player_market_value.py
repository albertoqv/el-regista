from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.enrichment import apply_enrichment
from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.ports import MarketValueProvider, PlayerRepository


@dataclass
class EnrichPlayerMarketValueUseCase:
    provider: MarketValueProvider
    repository: PlayerRepository

    def execute(self, player_id: int, player_name: str) -> IngestionResult:
        player = self.repository.get_player(player_id)
        birth_year = player.birth_year if player else None
        result = self.provider.get_market_value_history(player_name, birth_year)
        if result is None:
            return IngestionResult(
                ingested=0,
                skipped=[
                    SkippedPlayer(
                        player_id, player_name, "player not found in Transfermarkt"
                    )
                ],
            )

        if player is not None:
            apply_enrichment(self.repository, player, result)
        else:
            self.repository.save_market_value_history(player_id, result.points)
        return IngestionResult(ingested=1, skipped=[])
