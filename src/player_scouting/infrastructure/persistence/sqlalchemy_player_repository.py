from __future__ import annotations

from sqlalchemy.orm import Session

from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.models import (
    PlayerMarketValueModel,
    PlayerModel,
    PlayerSeasonStatisticsModel,
)

_STATISTICS_FIELDS = (
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "expected_goals",
    "passes_completed",
    "passes_attempted",
    "key_passes",
    "dribbles_completed",
    "dribbles_attempted",
    "tackles_won",
    "interceptions",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "red_cards",
)


class SqlAlchemyPlayerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_player(self, player_id: int) -> Player | None:
        model = self._session.get(PlayerModel, player_id)
        if model is None:
            return None
        return self._player_to_domain(model)

    def list_players(self) -> list[Player]:
        models = self._session.query(PlayerModel).all()
        return [self._player_to_domain(model) for model in models]

    def save_player(self, player: Player) -> None:
        model = self._session.get(PlayerModel, player.player_id)
        if model is None:
            model = PlayerModel(player_id=player.player_id)
            self._session.add(model)
        model.name = player.name
        model.position = player.position
        model.date_of_birth = player.date_of_birth
        model.photo_url = player.photo_url
        model.preferred_foot = player.preferred_foot
        self._session.flush()

    def save_season_statistics(
        self, player_id: int, season: Season, statistics: Statistics
    ) -> None:
        model = self._season_model(player_id, season)
        if model is None:
            model = PlayerSeasonStatisticsModel(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            self._session.add(model)
        for field_name in _STATISTICS_FIELDS:
            setattr(model, field_name, getattr(statistics, field_name))
        self._session.flush()

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None:
        model = self._season_model(player_id, season)
        if model is None:
            return None
        return self._statistics_to_domain(model)

    def list_seasons_for_player(self, player_id: int) -> list[Season]:
        models = (
            self._session.query(PlayerSeasonStatisticsModel)
            .filter_by(player_id=player_id)
            .all()
        )
        return [Season(model.competition, model.season_label) for model in models]

    def get_career_statistics(self, player_id: int) -> Statistics:
        models = (
            self._session.query(PlayerSeasonStatisticsModel)
            .filter_by(player_id=player_id)
            .all()
        )
        statistics = [self._statistics_to_domain(model) for model in models]
        return sum(statistics, Statistics(0, 0))

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]:
        models = self._session.query(PlayerSeasonStatisticsModel).all()
        entries = []
        for model in models:
            player = self.get_player(model.player_id)
            if player is not None:
                season = Season(model.competition, model.season_label)
                entries.append((player, season, self._statistics_to_domain(model)))
        return entries

    def save_market_value_history(
        self, player_id: int, points: list[MarketValuePoint]
    ) -> None:
        self._session.query(PlayerMarketValueModel).filter_by(
            player_id=player_id
        ).delete()
        for point in points:
            self._session.add(
                PlayerMarketValueModel(
                    player_id=player_id,
                    as_of_date=point.as_of,
                    amount_eur=point.amount_eur,
                    club=point.club,
                )
            )
        self._session.flush()

    def list_market_value_history(self, player_id: int) -> list[MarketValuePoint]:
        models = (
            self._session.query(PlayerMarketValueModel)
            .filter_by(player_id=player_id)
            .order_by(PlayerMarketValueModel.as_of_date)
            .all()
        )
        return [
            MarketValuePoint(model.as_of_date, model.amount_eur, model.club)
            for model in models
        ]

    def _season_model(
        self, player_id: int, season: Season
    ) -> PlayerSeasonStatisticsModel | None:
        return (
            self._session.query(PlayerSeasonStatisticsModel)
            .filter_by(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            .one_or_none()
        )

    @staticmethod
    def _player_to_domain(model: PlayerModel) -> Player:
        return Player(
            model.player_id,
            model.name,
            model.position,
            model.date_of_birth,
            photo_url=model.photo_url,
            preferred_foot=model.preferred_foot,
        )

    @staticmethod
    def _statistics_to_domain(model: PlayerSeasonStatisticsModel) -> Statistics:
        return Statistics(
            **{
                field_name: getattr(model, field_name)
                for field_name in _STATISTICS_FIELDS
            }
        )
