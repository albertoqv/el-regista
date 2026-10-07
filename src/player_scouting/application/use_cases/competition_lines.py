from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.ports import (
    CompetitionStatsRepository,
    DatasetCompetitionRow,
    PlayerRepository,
    TransfermarktDatasetProvider,
)
from player_scouting.application.use_cases.transfermarkt_dataset import (
    create_from_profile,
)
from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.season import BIG_FIVE

# Seasons read from the dataset: enough for a player's recent career.
DATASET_SINCE = 2019
# Playing here (or in the big five leagues) brings a player we did not have.
NOTABLE_COMPETITIONS = {"Champions League", "Europa League"}


@dataclass
class RecordCompetitionLinesUseCase:
    """Stores competition lines identified by Transfermarkt id (dataset or pages)."""

    players: PlayerRepository
    competitions: CompetitionStatsRepository

    def execute(self, rows: list[DatasetCompetitionRow]) -> IngestionResult:
        known = self.players.transfermarkt_index()
        merged: dict[tuple[int, str, str], CompetitionLine] = {}
        for row in rows:
            # Only players with a page here; the rest have nowhere to be shown.
            player_id = known.get(row.transfermarkt_id)
            if player_id is None:
                continue
            key = (player_id, row.line.competition, row.line.season_label)
            merged[key] = _added(merged[key], row.line) if key in merged else row.line
        lines: dict[int, list[CompetitionLine]] = defaultdict(list)
        for (player_id, _, _), line in merged.items():
            lines[player_id].append(line)
        self.competitions.save_competition_lines(dict(lines))
        return IngestionResult(ingested=len(merged))


def _added(first: CompetitionLine, second: CompetitionLine) -> CompetitionLine:
    """Two clubs' pages listing one player in the same competition: a mid-season
    move. One line, added up, under the club he played most for."""
    team = first.team if first.minutes_played >= second.minutes_played else second.team
    return replace(
        first,
        team=team,
        appearances=first.appearances + second.appearances,
        goals=first.goals + second.goals,
        assists=first.assists + second.assists,
        minutes_played=first.minutes_played + second.minutes_played,
        yellow_cards=first.yellow_cards + second.yellow_cards,
        red_cards=first.red_cards + second.red_cards,
    )


@dataclass
class IngestDatasetCompetitionsUseCase:
    provider: TransfermarktDatasetProvider
    players: PlayerRepository
    competitions: CompetitionStatsRepository

    def execute(self, since: int = DATASET_SINCE) -> IngestionResult:
        rows = self.provider.competition_rows(since)
        self._create_missing_stars(rows)
        return RecordCompetitionLinesUseCase(self.players, self.competitions).execute(
            rows
        )

    def _create_missing_stars(self, rows: list[DatasetCompetitionRow]) -> None:
        """Players we never had (left Europe before our league data, like Messi)
        but who played in the big five leagues or Europe: created from their
        dataset profile. Anyone else stays out, as before."""
        known = self.players.transfermarkt_index()
        wanted = {
            row.transfermarkt_id
            for row in rows
            if row.transfermarkt_id not in known
            and (
                row.line.competition in NOTABLE_COMPETITIONS
                or (row.line.kind == "league" and row.line.competition in BIG_FIVE)
            )
        }
        if not wanted:
            return
        for profile in self.provider.profiles():
            if profile.transfermarkt_id in wanted:
                create_from_profile(self.players, profile)
