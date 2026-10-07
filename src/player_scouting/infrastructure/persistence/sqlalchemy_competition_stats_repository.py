from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from player_scouting.domain.competitions import (
    CompetitionKind,
    CompetitionLine,
    sorted_lines,
)
from player_scouting.infrastructure.persistence.models import (
    PlayerCompetitionStatsModel,
)

# Rows per INSERT: one round trip each, whatever the number of players.
BATCH = 2000
_VALUES = (
    "kind",
    "team",
    "appearances",
    "goals",
    "assists",
    "minutes_played",
    "yellow_cards",
    "red_cards",
)


class SqlAlchemyCompetitionStatsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_competition_lines(
        self, lines_by_player: dict[int, list[CompetitionLine]]
    ) -> None:
        rows = [
            {
                "player_id": player_id,
                "competition": line.competition,
                "season_label": line.season_label,
                **{name: getattr(line, name) for name in _VALUES},
            }
            for player_id, lines in lines_by_player.items()
            for line in lines
        ]
        for start in range(0, len(rows), BATCH):
            statement = insert(PlayerCompetitionStatsModel).values(
                rows[start : start + BATCH]
            )
            self._session.execute(
                statement.on_conflict_do_update(
                    index_elements=["player_id", "competition", "season_label"],
                    set_={name: statement.excluded[name] for name in _VALUES},
                )
            )
        self._session.commit()

    def list_competition_lines(self, player_id: int) -> list[CompetitionLine]:
        models = self._session.scalars(
            select(PlayerCompetitionStatsModel).where(
                PlayerCompetitionStatsModel.player_id == player_id
            )
        )
        return sorted_lines(
            [
                CompetitionLine(
                    competition=model.competition,
                    kind=cast(CompetitionKind, model.kind),
                    season_label=model.season_label,
                    team=model.team,
                    appearances=model.appearances,
                    goals=model.goals,
                    assists=model.assists,
                    minutes_played=model.minutes_played,
                    yellow_cards=model.yellow_cards,
                    red_cards=model.red_cards,
                )
                for model in models
            ]
        )
