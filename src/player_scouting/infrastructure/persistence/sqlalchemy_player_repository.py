from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    ColumnElement,
    Integer,
    Select,
    and_,
    cast,
    func,
    nulls_last,
    select,
)
from sqlalchemy.orm import Session

from player_scouting.application.ports import (
    LeaderMetric,
    PlayerSort,
    PlayerSummary,
    SeasonEntry,
    SeasonLeader,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics
from player_scouting.infrastructure.persistence.models import (
    PlayerMarketValueModel,
    PlayerModel,
    PlayerSeasonAdvancedStatisticsModel,
    PlayerSeasonStatisticsModel,
)

Basic = PlayerSeasonStatisticsModel
Advanced = PlayerSeasonAdvancedStatisticsModel

# Columns of the basic (FBref) table.
_BASIC_FIELDS = (
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
    "minutes_played",
)
# Columns of the advanced (Understat) table.
_ADVANCED_FIELDS = (
    "expected_goals",
    "expected_assists",
    "key_passes",
    "xg_chain",
    "xg_buildup",
)
_ADVANCED_JOIN = and_(
    Advanced.player_id == Basic.player_id,
    Advanced.competition == Basic.competition,
    Advanced.season_label == Basic.season_label,
)


def _merged_column(field_name: str) -> ColumnElement[Any]:
    """SQL equivalent of Statistics.with_advanced for one field."""
    if field_name in ("expected_goals", "key_passes"):
        return func.coalesce(getattr(Advanced, field_name), getattr(Basic, field_name))
    if field_name in _ADVANCED_FIELDS:
        return func.coalesce(getattr(Advanced, field_name), 0)
    return getattr(Basic, field_name)


_CAREER_FIELDS = _BASIC_FIELDS + ("expected_assists", "xg_chain", "xg_buildup")


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
        statement = self._ranked_players(sort, query).limit(limit)
        summaries = []
        for row in self._session.execute(statement):
            values = row._mapping
            career = Statistics(
                **{field_name: values[field_name] or 0 for field_name in _CAREER_FIELDS}
            )
            summaries.append(
                PlayerSummary(
                    self._player_to_domain(values[PlayerModel]),
                    career,
                    values["latest_year"],
                )
            )
        return summaries

    def list_players_pending_enrichment(self, limit: int) -> list[Player]:
        statement = (
            self._ranked_players("recent", None)
            .where(PlayerModel.enrichment_checked_at.is_(None))
            .limit(limit)
        )
        return [
            self._player_to_domain(row._mapping[PlayerModel])
            for row in self._session.execute(statement)
        ]

    def mark_enrichment_checked(self, player_id: int) -> None:
        model = self._session.get(PlayerModel, player_id)
        if model is not None:
            model.enrichment_checked_at = datetime.now(UTC)
            self._session.flush()

    def set_understat_id(self, player_id: int, understat_id: int) -> None:
        model = self._session.get(PlayerModel, player_id)
        if model is not None:
            model.understat_id = understat_id
            self._session.flush()

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
        self,
        player_id: int,
        season: Season,
        statistics: Statistics,
        team: str | None = None,
    ) -> None:
        model = self._basic_model(player_id, season)
        if model is None:
            model = Basic(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            self._session.add(model)
        for field_name in _BASIC_FIELDS:
            setattr(model, field_name, getattr(statistics, field_name))
        model.team = team
        self._session.flush()

    def save_season_advanced(
        self, player_id: int, season: Season, advanced: AdvancedStatistics
    ) -> None:
        model = (
            self._session.query(Advanced)
            .filter_by(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            .one_or_none()
        )
        if model is None:
            model = Advanced(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            self._session.add(model)
        for field_name in _ADVANCED_FIELDS:
            setattr(model, field_name, getattr(advanced, field_name))
        self._session.flush()

    def get_season_statistics(
        self, player_id: int, season: Season
    ) -> Statistics | None:
        row = (
            self._session.query(Basic, Advanced)
            .outerjoin(Advanced, _ADVANCED_JOIN)
            .filter(
                Basic.player_id == player_id,
                Basic.competition == season.competition,
                Basic.season_label == season.label,
            )
            .one_or_none()
        )
        return self._merge(*row) if row else None

    def list_seasons_for_player(self, player_id: int) -> list[Season]:
        models = self._session.query(Basic).filter_by(player_id=player_id).all()
        return [Season(model.competition, model.season_label) for model in models]

    def get_season_team(self, player_id: int, season: Season) -> str | None:
        model = self._basic_model(player_id, season)
        return model.team if model else None

    def get_career_statistics(self, player_id: int) -> Statistics:
        rows = (
            self._session.query(Basic, Advanced)
            .outerjoin(Advanced, _ADVANCED_JOIN)
            .filter(Basic.player_id == player_id)
            .all()
        )
        return sum((self._merge(*row) for row in rows), Statistics(0, 0))

    def list_all_season_statistics(
        self,
    ) -> list[tuple[Player, Season, Statistics]]:
        return [
            (
                self._player_to_domain(player_model),
                Season(basic.competition, basic.season_label),
                self._merge(basic, advanced),
            )
            for basic, advanced, player_model in self._season_rows()
        ]

    def list_season_leaders(
        self,
        season_label: str,
        metric: LeaderMetric,
        limit: int,
        competition: str | None = None,
    ) -> list[SeasonLeader]:
        filters = [Basic.season_label == season_label]
        if competition is not None:
            filters.append(Basic.competition == competition)
        rows = (
            self._session.query(Basic, Advanced, PlayerModel)
            .join(PlayerModel, PlayerModel.player_id == Basic.player_id)
            .outerjoin(Advanced, _ADVANCED_JOIN)
            .filter(*filters)
            .order_by(_merged_column(metric).desc(), PlayerModel.name)
            .limit(limit)
            .all()
        )
        return [
            SeasonLeader(
                self._player_to_domain(player_model),
                Season(basic.competition, basic.season_label),
                basic.team,
                self._merge(basic, advanced),
            )
            for basic, advanced, player_model in rows
        ]

    def list_season_entries(self, season: Season) -> list[SeasonEntry]:
        rows = self._season_rows(
            Basic.competition == season.competition,
            Basic.season_label == season.label,
        )
        return [
            SeasonEntry(
                self._player_to_domain(player_model),
                basic.team,
                self._merge(basic, advanced),
            )
            for basic, advanced, player_model in rows
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

    def _ranked_players(self, sort: PlayerSort, query: str | None) -> Select:
        season_year = cast(func.substring(Basic.season_label, r"\d{4}"), Integer)
        totals = (
            select(
                Basic.player_id.label("player_id"),
                *[
                    func.sum(_merged_column(field_name)).label(field_name)
                    for field_name in _CAREER_FIELDS
                ],
                func.max(season_year).label("latest_year"),
            )
            .select_from(Basic)
            .outerjoin(Advanced, _ADVANCED_JOIN)
            .group_by(Basic.player_id)
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
        return statement.order_by(*order_by)

    def _season_rows(
        self, *filters: ColumnElement[bool]
    ) -> list[tuple[Basic, Advanced | None, PlayerModel]]:
        rows = (
            self._session.query(Basic, Advanced, PlayerModel)
            .join(PlayerModel, PlayerModel.player_id == Basic.player_id)
            .outerjoin(Advanced, _ADVANCED_JOIN)
            .filter(*filters)
            .all()
        )
        return [(basic, advanced, player) for basic, advanced, player in rows]

    def _basic_model(self, player_id: int, season: Season) -> Basic | None:
        return (
            self._session.query(Basic)
            .filter_by(
                player_id=player_id,
                competition=season.competition,
                season_label=season.label,
            )
            .one_or_none()
        )

    @staticmethod
    def _merge(basic: Basic, advanced: Advanced | None) -> Statistics:
        statistics = Statistics(
            **{field_name: getattr(basic, field_name) for field_name in _BASIC_FIELDS}
        )
        if advanced is None:
            return statistics
        return statistics.with_advanced(
            AdvancedStatistics(
                **{
                    field_name: getattr(advanced, field_name)
                    for field_name in _ADVANCED_FIELDS
                }
            )
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
