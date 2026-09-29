from __future__ import annotations

from sqlalchemy import Integer, cast, func, nulls_last, select
from sqlalchemy.orm import Session

from player_scouting.application.ports import PlayerSort, PlayerSummary
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

    def search_player_summaries(
        self, query: str | None, sort: PlayerSort, limit: int
    ) -> list[PlayerSummary]:
        stats = PlayerSeasonStatisticsModel
        season_year = cast(func.substring(stats.season_label, r"\d{4}"), Integer)
        totals = (
            select(
                stats.player_id.label("player_id"),
                *[
                    func.sum(getattr(stats, field_name)).label(field_name)
                    for field_name in _STATISTICS_FIELDS
                ],
                func.max(season_year).label("latest_year"),
            )
            .group_by(stats.player_id)
            .subquery()
        )
        goals = func.coalesce(totals.c.goals, 0)
        assists = func.coalesce(totals.c.assists, 0)
        order_by = {
            "goals": (goals.desc(), PlayerModel.name),
            "assists": (assists.desc(), PlayerModel.name),
            "recent": (
                nulls_last(totals.c.latest_year.desc()),
                (goals + assists).desc(),
                PlayerModel.name,
            ),
        }[sort]

        statement = select(PlayerModel, totals).outerjoin(
            totals, totals.c.player_id == PlayerModel.player_id
        )
        if query:
            statement = statement.where(PlayerModel.name.ilike(f"%{query}%"))
        rows = self._session.execute(statement.order_by(*order_by).limit(limit))

        summaries = []
        for row in rows:
            values = row._mapping
            career = Statistics(
                **{
                    field_name: values[field_name] or 0
                    for field_name in _STATISTICS_FIELDS
                }
            )
            summaries.append(
                PlayerSummary(
                    self._player_to_domain(values[PlayerModel]),
                    career,
                    values["latest_year"],
                )
            )
        return summaries

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
        model.birth_year = player.birth_year
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
        rows = (
            self._session.query(PlayerSeasonStatisticsModel, PlayerModel)
            .join(
                PlayerModel,
                PlayerModel.player_id == PlayerSeasonStatisticsModel.player_id,
            )
            .all()
        )
        return [
            (
                self._player_to_domain(player_model),
                Season(stats_model.competition, stats_model.season_label),
                self._statistics_to_domain(stats_model),
            )
            for stats_model, player_model in rows
        ]

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
            birth_year=model.birth_year,
        )

    @staticmethod
    def _statistics_to_domain(model: PlayerSeasonStatisticsModel) -> Statistics:
        return Statistics(
            **{
                field_name: getattr(model, field_name)
                for field_name in _STATISTICS_FIELDS
            }
        )
