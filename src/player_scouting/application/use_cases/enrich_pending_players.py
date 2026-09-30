from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from player_scouting.application.enrichment import apply_enrichment
from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.ports import (
    EnrichmentUnavailableError,
    MarketValueProvider,
    PlayerRepository,
)

# Each player costs three requests to the source; keep the pace polite.
PAUSE_BETWEEN_PLAYERS_SECONDS = 1.0


@dataclass
class EnrichPendingPlayersUseCase:
    provider: MarketValueProvider
    repository: PlayerRepository
    pause: Callable[[float], None] = field(default=time.sleep)

    def execute(self, limit: int) -> IngestionResult:
        ingested = 0
        skipped: list[SkippedPlayer] = []
        players = self.repository.list_players_pending_enrichment(limit)
        for index, player in enumerate(players):
            if index:
                self.pause(PAUSE_BETWEEN_PLAYERS_SECONDS)
            try:
                result = self.provider.get_market_value_history(
                    player.name, player.birth_year
                )
            except EnrichmentUnavailableError:
                break
            if result is None:
                skipped.append(
                    SkippedPlayer(
                        player.player_id, player.name, "not found in Transfermarkt"
                    )
                )
            else:
                apply_enrichment(self.repository, player, result)
                ingested += 1
            self.repository.mark_enrichment_checked(player.player_id)
        return IngestionResult(ingested=ingested, skipped=skipped)
