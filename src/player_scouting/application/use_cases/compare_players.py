from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.similarity_calculator import SimilarityCalculator


@dataclass
class ComparePlayersUseCase:
    repository: PlayerRepository
    calculator: SimilarityCalculator

    def execute(self, player_id_a: int, player_id_b: int) -> Comparison:
        entry_a = self.repository.get(player_id_a)
        if entry_a is None:
            raise PlayerNotFoundError(f"No player found with id {player_id_a}")
        entry_b = self.repository.get(player_id_b)
        if entry_b is None:
            raise PlayerNotFoundError(f"No player found with id {player_id_b}")

        player_a, stats_a = entry_a
        player_b, stats_b = entry_b
        similarity_score = self.calculator.total_similarity(stats_a, stats_b)
        return Comparison(player_a, player_b, similarity_score)
