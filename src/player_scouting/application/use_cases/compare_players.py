from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.domain.statistics import Statistics


@dataclass
class ComparePlayersUseCase:
    repository: PlayerRepository
    calculator: SimilarityCalculator

    def execute(
        self,
        player_id_a: int,
        player_id_b: int,
        season_a: Season | None = None,
        season_b: Season | None = None,
    ) -> Comparison:
        player_a, stats_a = self._resolve(player_id_a, season_a)
        player_b, stats_b = self._resolve(player_id_b, season_b)
        similarity_score = self.calculator.total_similarity(stats_a, stats_b)
        return Comparison(player_a, player_b, similarity_score)

    def _resolve(
        self, player_id: int, season: Season | None
    ) -> tuple[Player, Statistics]:
        player = self.repository.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError(f"No player found with id {player_id}")

        if season is None:
            return player, self.repository.get_career_statistics(player_id)

        statistics = self.repository.get_season_statistics(player_id, season)
        if statistics is None:
            raise PlayerNotFoundError(
                f"No statistics found for player {player_id} in {season}"
            )
        return player, statistics
