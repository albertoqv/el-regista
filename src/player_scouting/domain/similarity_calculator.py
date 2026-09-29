from dataclasses import fields

from player_scouting.domain.statistics import Statistics
from player_scouting.domain.value_objects import SimilarityScore


# Playing time is context, not playing style: two players are not less alike
# because one of them played more minutes.
_EXCLUDED_FIELDS = frozenset({"minutes_played"})


class SimilarityCalculator:
    def similarity_metric(self, value_a: int | float, value_b: int | float) -> float:
        if value_a == value_b:
            return 1
        else:
            result = 1 - abs(value_a - value_b) / max(value_a, value_b)
            return result

    def total_similarity(
        self, player1_stats: Statistics, player2_stats: Statistics
    ) -> SimilarityScore:
        scores = []
        for field in fields(Statistics):
            if field.name in _EXCLUDED_FIELDS:
                continue
            value_a = getattr(player1_stats, field.name)
            value_b = getattr(player2_stats, field.name)
            if value_a == 0 and value_b == 0:
                continue
            scores.append(self.similarity_metric(value_a, value_b))

        average = sum(scores) / len(scores) if scores else 1.0
        return SimilarityScore(round(average * 100))
