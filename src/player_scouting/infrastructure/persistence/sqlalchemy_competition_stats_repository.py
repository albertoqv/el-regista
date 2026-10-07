from __future__ import annotations

from typing import cast

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from player_scouting.domain.career import AgePoint
from player_scouting.domain.competitions import (
    CompetitionKind,
    CompetitionLine,
    sorted_lines,
)
from player_scouting.infrastructure.persistence.models import (
    PlayerCompetitionStatsModel,
)

# A season counts for the benchmark from this many club minutes: a regular's level.
BENCHMARK_MINUTES = 900
# Grouped inside Postgres: one row per age travels, not every player's seasons.
_AGE_BENCHMARK = text(
    """
    WITH seasons AS (
        SELECT player_id, season_label,
               SUM(goals + assists) AS output, SUM(minutes_played) AS minutes
        FROM player_competition_stats
        WHERE kind <> 'national'
        GROUP BY player_id, season_label
    ), aged AS (
        SELECT CAST(s.season_label AS INTEGER)
                 - COALESCE(CAST(EXTRACT(YEAR FROM p.date_of_birth) AS INTEGER),
                            p.birth_year) AS age,
               s.output, s.minutes
        FROM seasons s JOIN players p ON p.player_id = s.player_id
        WHERE p.position = :position AND s.minutes >= :minutes
    )
    SELECT age, SUM(output) * 90.0 / SUM(minutes) AS per90, COUNT(*) AS players
    FROM aged
    WHERE age BETWEEN 15 AND 42
    GROUP BY age
    ORDER BY age
    """
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
        return sorted_lines([_to_line(model) for model in models])

    def age_benchmark(self, position: str) -> list[AgePoint]:
        rows = self._session.execute(
            _AGE_BENCHMARK, {"position": position, "minutes": BENCHMARK_MINUTES}
        )
        return [
            AgePoint(age=row.age, per90=round(float(row.per90), 3), players=row.players)
            for row in rows
        ]

    def list_competition_lines_since(
        self, season_label: str
    ) -> dict[int, list[CompetitionLine]]:
        lines: dict[int, list[CompetitionLine]] = {}
        models = self._session.scalars(
            select(PlayerCompetitionStatsModel).where(
                PlayerCompetitionStatsModel.season_label >= season_label
            )
        )
        for model in models:
            lines.setdefault(model.player_id, []).append(_to_line(model))
        return lines


def _to_line(model: PlayerCompetitionStatsModel) -> CompetitionLine:
    return CompetitionLine(
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
