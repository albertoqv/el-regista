from __future__ import annotations

from dataclasses import dataclass, replace

from player_scouting.application.league_ingestion_job import (
    LeagueIngestionJobRepository,
)
from player_scouting.application.ports import LeaguePlayersProvider, PlayerRepository
from player_scouting.domain.entities import Player

UNKNOWN_POSITION = "Unknown"


@dataclass
class LeagueIngestionBatchSummary:
    pages_processed: int
    players_ingested: int


@dataclass
class ProcessLeagueIngestionBatchUseCase:
    provider: LeaguePlayersProvider
    player_repository: PlayerRepository
    job_repository: LeagueIngestionJobRepository

    def execute(self, request_budget: int) -> LeagueIngestionBatchSummary:
        pages_processed = 0
        players_ingested = 0

        while pages_processed < request_budget:
            job = self.job_repository.next_pending_job()
            if job is None:
                break

            page = self.provider.get_players_page(
                job.league_id, job.season_year, job.next_page
            )
            for result in page.players:
                player = Player(
                    result.player_id,
                    result.name,
                    result.position or UNKNOWN_POSITION,
                    result.date_of_birth,
                    photo_url=result.photo_url,
                )
                self.player_repository.save_player(player)
                self.player_repository.save_season_statistics(
                    player.player_id, result.season, result.statistics
                )
                players_ingested += 1

            self.job_repository.save_job(
                replace(job, next_page=job.next_page + 1, total_pages=page.total_pages)
            )
            pages_processed += 1

        return LeagueIngestionBatchSummary(
            pages_processed=pages_processed, players_ingested=players_ingested
        )
