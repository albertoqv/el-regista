from __future__ import annotations

from dataclasses import dataclass, field

from player_scouting.application.ports import (
    BirthDateProvider,
    CompetitionStatisticsProvider,
    PlayerRepository,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics

UNKNOWN_POSITION = "Unknown"


@dataclass
class SkippedPlayer:
    player_id: int
    name: str
    reason: str


@dataclass
class IngestionResult:
    ingested: int
    skipped: list[SkippedPlayer] = field(default_factory=list)


@dataclass
class IngestCompetitionUseCase:
    statistics_provider: CompetitionStatisticsProvider
    birth_date_provider: BirthDateProvider
    repository: PlayerRepository

    def execute(self, competition_id: int, season_id: int) -> IngestionResult:
        player_stats = self.statistics_provider.get_statistics(
            competition_id, season_id
        )

        ingested = 0
        skipped: list[SkippedPlayer] = []
        for stats in player_stats:
            birth_date = self.birth_date_provider.find(stats.name, stats.nationality)
            if birth_date is None:
                skipped.append(
                    SkippedPlayer(
                        stats.player_id, stats.name, "no reliable birth date found"
                    )
                )
                continue

            player = Player(
                stats.player_id,
                stats.name,
                stats.position or UNKNOWN_POSITION,
                birth_date,
            )
            self.repository.save(player, Statistics(stats.goals, stats.assists))
            ingested += 1

        return IngestionResult(ingested=ingested, skipped=skipped)
