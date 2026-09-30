from __future__ import annotations

from dataclasses import fields
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from player_scouting.application.ports import MatchStats
from player_scouting.infrastructure.persistence.models import MatchStatsModel

_FIELDS = tuple(f.name for f in fields(MatchStats))


def _to_domain(model: MatchStatsModel) -> MatchStats:
    return MatchStats(**{name: getattr(model, name) for name in _FIELDS})


class SqlAlchemyMatchStatsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_match_stats(self, matches: list[MatchStats]) -> None:
        # merge = upsert on (competition, date, home, away): fixtures get results.
        for match in matches:
            self._session.merge(
                MatchStatsModel(**{name: getattr(match, name) for name in _FIELDS})
            )
        self._session.flush()

    def list_match_stats(
        self, competition: str, season_labels: list[str]
    ) -> list[MatchStats]:
        statement = (
            select(MatchStatsModel)
            .where(
                MatchStatsModel.competition == competition,
                MatchStatsModel.season_label.in_(season_labels),
            )
            .order_by(MatchStatsModel.played_on, MatchStatsModel.home_team)
        )
        return [_to_domain(model) for model in self._session.scalars(statement)]

    def find_upcoming(
        self, competition: str, played_on: date, home_team: str, away_team: str
    ) -> MatchStats | None:
        model = self._session.get(
            MatchStatsModel, (competition, played_on, home_team, away_team)
        )
        return _to_domain(model) if model else None
