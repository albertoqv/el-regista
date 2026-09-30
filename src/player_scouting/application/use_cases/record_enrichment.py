from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.enrichment import apply_enrichment
from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import MarketValueHistoryResult, PlayerRepository


@dataclass
class RecordEnrichmentUseCase:
    """Stores an enrichment looked up outside the API (the source blocks our IP)."""

    repository: PlayerRepository

    def execute(self, player_id: int, result: MarketValueHistoryResult | None) -> None:
        player = self.repository.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError(f"No player found with id {player_id}")
        if result is not None:
            apply_enrichment(self.repository, player, result)
        self.repository.mark_enrichment_checked(player_id)
