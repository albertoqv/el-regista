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
    literal,
    nulls_last,
    or_,
    select,
)
from sqlalchemy.orm import Session

from player_scouting.application.ports import (
    LeaderMetric,
    PlayerSort,
    PlayerSummary,
    SeasonEntry,
    SeasonRecord,
)
from player_scouting.application.team_names import renamed
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


# pg_trgm word_similarity of the query with the closest stretch of a name: a missing or
# doubled letter keeps it well above this ("mbape" ~0.8); unrelated names stay below.
SEARCH_LIKENESS = 0.5


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
        model.height_cm = player.height_cm
        model.detailed_position = player.detailed_position
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

    def rename_season_team(self, season: Season, old: str, new: str) -> None:
        models = (
            self._session.query(Basic)
            .filter(
                Basic.competition == season.competition,
                Basic.season_label == season.label,
                Basic.team.contains(old),
            )
            .all()
        )
        for model in models:
            if model.team is not None:
                model.team = renamed(model.team, old, new)
        self._session.flush()

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
        competitions: tuple[str, ...] | None = None,
    ) -> list[SeasonRecord]:
        filters = [Basic.season_label == season_label]
        if competition is not None:
            filters.append(Basic.competition == competition)
        if competitions is not None:
            filters.append(Basic.competition.in_(competitions))
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
            SeasonRecord(
                self._player_to_domain(player_model),
                Season(basic.competition, basic.season_label),
                basic.team,
                self._merge(basic, advanced),
            )
            for basic, advanced, player_model in rows
        ]

    def list_season_records(self, season_labels: list[str]) -> list[SeasonRecord]:
        return [
            SeasonRecord(
                self._player_to_domain(player_model),
                Season(basic.competition, basic.season_label),
                basic.team,
                self._merge(basic, advanced),
            )
            for basic, advanced, player_model in self._season_rows(
                Basic.season_label.in_(season_labels)
            )
        ]

    def set_transfermarkt_id(self, player_id: int, transfermarkt_id: int) -> None:
        model = self._session.get(PlayerModel, player_id)
        if model is not None:
            model.transfermarkt_id = transfermarkt_id
            self._session.flush()

    def transfermarkt_index(self) -> dict[int, int]:
        rows = self._session.execute(
            select(PlayerModel.transfermarkt_id, PlayerModel.player_id).where(
                PlayerModel.transfermarkt_id.is_not(None)
            )
        )
        return {tm_id: player_id for tm_id, player_id in rows if tm_id is not None}

    def find_by_understat_ids(self, understat_ids: list[int]) -> dict[int, Player]:
        models = self._session.scalars(
            select(PlayerModel).where(PlayerModel.understat_id.in_(understat_ids))
        )
        return {
            model.understat_id: self._player_to_domain(model)
            for model in models
            if model.understat_id is not None
        }

    def list_duplicate_groups(self) -> list[list[int]]:
        """Players that are the same person: FBref spelled them differently."""
        shared = (
            select(PlayerModel.understat_id)
            .where(PlayerModel.understat_id.is_not(None))
            .group_by(PlayerModel.understat_id)
            .having(func.count() > 1)
        )
        groups: dict[int, list[int]] = {}
        for player_id, understat_id in self._session.execute(
            select(PlayerModel.player_id, PlayerModel.understat_id)
            .where(PlayerModel.understat_id.in_(shared))
            .order_by(PlayerModel.player_id)
        ):
            if understat_id is not None:
                groups.setdefault(understat_id, []).append(player_id)
        return sorted(groups.values())

    def merge_players(self, keep: int, remove: int) -> None:
        self._move_season_rows(Basic, keep, remove)
        self._move_season_rows(Advanced, keep, remove)
        values = self._session.query(PlayerMarketValueModel)
        if values.filter_by(player_id=keep).count():
            values.filter_by(player_id=remove).delete()
        else:
            values.filter_by(player_id=remove).update({"player_id": keep})
        kept = self._session.get(PlayerModel, keep)
        removed = self._session.get(PlayerModel, remove)
        if kept is not None and removed is not None:
            for field in (
                "photo_url",
                "date_of_birth",
                "preferred_foot",
                "understat_id",
            ):
                if getattr(kept, field) is None:
                    setattr(kept, field, getattr(removed, field))
            self._session.flush()
            self._session.delete(removed)
        self._session.flush()

    def _move_season_rows[Row: (Basic, Advanced)](
        self, model: type[Row], keep: int, remove: int
    ) -> None:
        """Hands the removed player's seasons over; the kept player's rows win."""
        kept_seasons = {
            (row.competition, row.season_label)
            for row in self._session.query(model).filter_by(player_id=keep)
        }
        for row in self._session.query(model).filter_by(player_id=remove).all():
            if (row.competition, row.season_label) in kept_seasons:
                self._session.delete(row)
            else:
                row.player_id = keep

    def latest_market_values(self) -> dict[int, MarketValuePoint]:
        Value = PlayerMarketValueModel
        latest = (
            select(Value.player_id, func.max(Value.as_of_date).label("as_of"))
            .group_by(Value.player_id)
            .subquery()
        )
        rows = self._session.execute(
            select(Value).join(
                latest,
                and_(
                    Value.player_id == latest.c.player_id,
                    Value.as_of_date == latest.c.as_of,
                ),
            )
        ).scalars()
        return {
            row.player_id: MarketValuePoint(row.as_of_date, row.amount_eur, row.club)
            for row in rows
        }

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
            # Accents and case do not matter ("dembele"), and close spellings are
            # found too ("mbape"): exact matches first, then the most alike.
            name = func.f_unaccent(func.lower(PlayerModel.name))
            wanted = func.f_unaccent(func.lower(literal(query)))
            contains = name.contains(wanted)
            likeness = func.word_similarity(wanted, name)
            statement = statement.where(or_(contains, likeness >= SEARCH_LIKENESS))
            order_by = (contains.desc(), likeness.desc(), *order_by)
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
            height_cm=model.height_cm,
            detailed_position=model.detailed_position,
        )
