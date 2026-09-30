from __future__ import annotations

from dataclasses import replace

from player_scouting.application.ports import MarketValueHistoryResult, PlayerRepository
from player_scouting.domain.entities import Player


def apply_enrichment(
    repository: PlayerRepository, player: Player, result: MarketValueHistoryResult
) -> None:
    """Stores what the enrichment source found without erasing what it did not."""
    repository.save_player(
        replace(
            player,
            photo_url=result.photo_url or player.photo_url,
            date_of_birth=result.date_of_birth or player.date_of_birth,
            preferred_foot=result.preferred_foot or player.preferred_foot,
        )
    )
    if result.points:
        repository.save_market_value_history(player.player_id, result.points)
