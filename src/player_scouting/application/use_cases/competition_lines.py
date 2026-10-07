from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from player_scouting.application.ingestion_result import IngestionResult
from player_scouting.application.ports import (
    CompetitionStatsRepository,
    DatasetCompetitionRow,
    PlayerRepository,
    TransfermarktDatasetProvider,
)
from player_scouting.domain.competitions import CompetitionLine

# Seasons read from the dataset: enough for a player's recent career.
DATASET_SINCE = 2019


@dataclass
class RecordCompetitionLinesUseCase:
    """Stores competition lines identified by Transfermarkt id (dataset or pages)."""

    players: PlayerRepository
    competitions: CompetitionStatsRepository

    def execute(self, rows: list[DatasetCompetitionRow]) -> IngestionResult:
        known = self.players.transfermarkt_index()
        lines: dict[int, list[CompetitionLine]] = defaultdict(list)
        for row in rows:
            # Only players with a page here; the rest have nowhere to be shown.
            player_id = known.get(row.transfermarkt_id)
            if player_id is not None:
                lines[player_id].append(row.line)
        self.competitions.save_competition_lines(dict(lines))
        return IngestionResult(ingested=sum(len(group) for group in lines.values()))


@dataclass
class IngestDatasetCompetitionsUseCase:
    provider: TransfermarktDatasetProvider
    players: PlayerRepository
    competitions: CompetitionStatsRepository

    def execute(self, since: int = DATASET_SINCE) -> IngestionResult:
        return RecordCompetitionLinesUseCase(self.players, self.competitions).execute(
            self.provider.competition_rows(since)
        )
