from __future__ import annotations

from sqlalchemy.orm import Session

from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.models import PlayerModel


class SqlAlchemyPlayerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, player_id: int) -> tuple[Player, Statistics] | None:
        model = self._session.get(PlayerModel, player_id)
        if model is None:
            return None
        return self._to_domain(model)

    def list_all(self) -> list[tuple[Player, Statistics]]:
        models = self._session.query(PlayerModel).all()
        return [self._to_domain(model) for model in models]

    def save(self, player: Player, statistics: Statistics) -> None:
        model = self._session.get(PlayerModel, player.player_id)
        if model is None:
            model = PlayerModel(player_id=player.player_id)
            self._session.add(model)
        model.name = player.name
        model.position = player.position
        model.date_of_birth = player.date_of_birth
        model.goals = statistics.goals
        model.assists = statistics.assists
        self._session.flush()

    @staticmethod
    def _to_domain(model: PlayerModel) -> tuple[Player, Statistics]:
        player = Player(
            model.player_id, model.name, model.position, model.date_of_birth
        )
        statistics = Statistics(model.goals, model.assists)
        return player, statistics
