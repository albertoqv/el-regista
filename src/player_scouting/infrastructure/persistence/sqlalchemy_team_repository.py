from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from player_scouting.application.ports import Fixture, TeamMatch
from player_scouting.infrastructure.persistence.models import (
    FixtureModel,
    TeamMatchModel,
)

_FIXTURE_FIELDS = (
    "match_id",
    "competition",
    "season_label",
    "kickoff",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "home_xg",
    "away_xg",
)
_TEAM_MATCH_FIELDS = (
    "match_id",
    "competition",
    "season_label",
    "played_on",
    "team",
    "opponent",
    "home",
    "goals_for",
    "goals_against",
    "xg_for",
    "xg_against",
    "npxg_for",
    "npxg_against",
    "ppda",
    "ppda_allowed",
    "deep",
    "deep_allowed",
    "xpts",
    "result",
)


class SqlAlchemyTeamRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_team_season(
        self, fixtures: list[Fixture], team_matches: list[TeamMatch]
    ) -> None:
        # merge = insert or update: kick-off times move and results arrive.
        for fixture in fixtures:
            self._session.merge(
                FixtureModel(**{f: getattr(fixture, f) for f in _FIXTURE_FIELDS})
            )
        for match in team_matches:
            self._session.merge(
                TeamMatchModel(**{f: getattr(match, f) for f in _TEAM_MATCH_FIELDS})
            )
        self._session.flush()

    def list_team_matches(
        self, season_labels: list[str], competition: str | None = None
    ) -> list[TeamMatch]:
        statement = (
            select(TeamMatchModel)
            .where(TeamMatchModel.season_label.in_(season_labels))
            .order_by(TeamMatchModel.played_on, TeamMatchModel.match_id)
        )
        if competition is not None:
            statement = statement.where(TeamMatchModel.competition == competition)
        return [
            TeamMatch(**{f: getattr(model, f) for f in _TEAM_MATCH_FIELDS})
            for model in self._session.scalars(statement)
        ]

    def list_fixtures(
        self,
        competition: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Fixture]:
        statement = select(FixtureModel).order_by(
            FixtureModel.kickoff, FixtureModel.match_id
        )
        if competition is not None:
            statement = statement.where(FixtureModel.competition == competition)
        if start is not None:
            statement = statement.where(FixtureModel.kickoff >= start)
        if end is not None:
            statement = statement.where(FixtureModel.kickoff <= end)
        return [
            Fixture(**{f: getattr(model, f) for f in _FIXTURE_FIELDS})
            for model in self._session.scalars(statement)
        ]
