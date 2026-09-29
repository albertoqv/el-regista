from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.similarity_calculator import SimilarityCalculator


@dataclass
class FindSimilarPlayersUseCase:
    repository: PlayerRepository
    calculator: SimilarityCalculator

    def execute(self, player_id: int, top_n: int = 5) -> list[Comparison]:
        target_entry = self.repository.get(player_id)
        if target_entry is None:
            raise PlayerNotFoundError(f"No player found with id {player_id}")
        target_player, target_stats = target_entry

        comparisons = [
            Comparison(
                target_player,
                candidate_player,
                self.calculator.total_similarity(target_stats, candidate_stats),
            )
            for candidate_player, candidate_stats in self.repository.list_all()
            if candidate_player != target_player
        ]

        comparisons.sort(key=lambda c: c.similarity_score.percentage, reverse=True)
        return comparisons[:top_n]
