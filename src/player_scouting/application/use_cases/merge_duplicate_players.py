from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.entities import Player


def choose_kept(candidates: list[tuple[Player, int]]) -> Player:
    """Keeps the enriched record (photo), else the one with the latest season."""
    player, _ = max(
        candidates,
        key=lambda item: (item[0].photo_url is not None, item[1], item[0].player_id),
    )
    return player


@dataclass
class MergeDuplicatePlayersUseCase:
    repository: PlayerRepository

    def execute(self) -> int:
        merged = 0
        for group in self.repository.list_duplicate_groups():
            candidates = []
            for player_id in group:
                player = self.repository.get_player(player_id)
                if player is None:
                    continue
                years = [
                    s.start_year or 0
                    for s in self.repository.list_seasons_for_player(player_id)
                ]
                candidates.append((player, max(years, default=0)))
            if len(candidates) < 2:
                continue
            kept = choose_kept(candidates)
            for player, _ in candidates:
                if player.player_id != kept.player_id:
                    self.repository.merge_players(kept.player_id, player.player_id)
                    merged += 1
        return merged
