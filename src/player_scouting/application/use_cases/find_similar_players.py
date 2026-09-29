from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import PlayerRepository
from player_scouting.domain.comparison import Comparison
from player_scouting.domain.season import Season
from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.domain.statistics import Statistics


@dataclass
class SimilarPlayerMatch:
    comparison: Comparison
    candidate_season: Season


@dataclass
class FindSimilarPlayersUseCase:
    repository: PlayerRepository
    calculator: SimilarityCalculator

    def execute(
        self, player_id: int, season: Season | None = None, top_n: int = 5
    ) -> list[SimilarPlayerMatch]:
        target_player = self.repository.get_player(player_id)
        if target_player is None:
            raise PlayerNotFoundError(f"No player found with id {player_id}")

        target_stats: Statistics
        if season is None:
            target_stats = self.repository.get_career_statistics(player_id)
        else:
            season_stats = self.repository.get_season_statistics(player_id, season)
            if season_stats is None:
                raise PlayerNotFoundError(
                    f"No statistics found for player {player_id} in {season}"
                )
            target_stats = season_stats

        matches = [
            SimilarPlayerMatch(
                comparison=Comparison(
                    target_player,
                    candidate_player,
                    self.calculator.total_similarity(target_stats, candidate_stats),
                ),
                candidate_season=candidate_season,
            )
            for candidate_player, candidate_season, candidate_stats in (
                self.repository.list_all_season_statistics()
            )
            if candidate_player != target_player
        ]

        matches.sort(
            key=lambda match: match.comparison.similarity_score.percentage,
            reverse=True,
        )
        return matches[:top_n]
