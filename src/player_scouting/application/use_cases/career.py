from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.exceptions import PlayerNotFoundError
from player_scouting.application.ports import (
    CompetitionStatsRepository,
    PlayerRepository,
)
from player_scouting.domain.career import AgePoint, CareerPoint, career_by_age


@dataclass(frozen=True)
class CareerCurve:
    position: str
    points: list[CareerPoint]
    benchmark: list[AgePoint]


@dataclass
class CareerCurveUseCase:
    players: PlayerRepository
    competitions: CompetitionStatsRepository

    def execute(self, player_id: int) -> CareerCurve:
        player = self.players.get_player(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id)
        born = player.date_of_birth.year if player.date_of_birth else player.birth_year
        return CareerCurve(
            position=player.position,
            points=career_by_age(
                self.competitions.list_competition_lines(player_id), born
            ),
            benchmark=self.competitions.age_benchmark(player.position),
        )
