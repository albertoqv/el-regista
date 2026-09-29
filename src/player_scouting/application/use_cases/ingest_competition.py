from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.ingestion_result import IngestionResult, SkippedPlayer
from player_scouting.application.ports import (
    BirthDateProvider,
    CompetitionStatisticsProvider,
    PlayerRepository,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.statistics import Statistics

UNKNOWN_POSITION = "Unknown"


@dataclass
class IngestCompetitionUseCase:
    statistics_provider: CompetitionStatisticsProvider
    birth_date_provider: BirthDateProvider
    repository: PlayerRepository

    def execute(self, competition_id: int, season_id: int) -> IngestionResult:
        result = self.statistics_provider.get_statistics(competition_id, season_id)

        ingested = 0
        skipped: list[SkippedPlayer] = []
        for stats in result.players:
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
            statistics = Statistics(
                goals=stats.goals,
                assists=stats.assists,
                shots=stats.shots,
                shots_on_target=stats.shots_on_target,
                expected_goals=stats.expected_goals,
                passes_completed=stats.passes_completed,
                passes_attempted=stats.passes_attempted,
                key_passes=stats.key_passes,
                dribbles_completed=stats.dribbles_completed,
                dribbles_attempted=stats.dribbles_attempted,
                tackles_won=stats.tackles_won,
                interceptions=stats.interceptions,
                fouls_committed=stats.fouls_committed,
                fouls_won=stats.fouls_won,
                yellow_cards=stats.yellow_cards,
                red_cards=stats.red_cards,
            )
            self.repository.save_player(player)
            self.repository.save_season_statistics(
                player.player_id, result.season, statistics
            )
            ingested += 1

        return IngestionResult(ingested=ingested, skipped=skipped)
