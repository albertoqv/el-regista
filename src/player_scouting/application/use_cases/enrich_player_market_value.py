from __future__ import annotations

from dataclasses import dataclass, replace

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.ports import MarketValueProvider, PlayerRepository


@dataclass
class EnrichPlayerMarketValueUseCase:
    provider: MarketValueProvider
    repository: PlayerRepository

    def execute(self, player_id: int, player_name: str) -> IngestionResult:
        result = self.provider.get_market_value_history(player_name)
        if result is None:
            return IngestionResult(
                ingested=0,
                skipped=[
                    SkippedPlayer(
                        player_id, player_name, "player not found in Transfermarkt"
                    )
                ],
            )

        player = self.repository.get_player(player_id)
        if player is not None:
            self.repository.save_player(
                replace(player, preferred_foot=result.preferred_foot)
            )
        self.repository.save_market_value_history(player_id, result.points)
        return IngestionResult(ingested=1, skipped=[])
