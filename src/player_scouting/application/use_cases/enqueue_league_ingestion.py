from __future__ import annotations

from dataclasses import dataclass

from player_scouting.application.league_ingestion_job import (
    LeagueIngestionJob,
    LeagueIngestionJobRepository,
)


@dataclass
class EnqueueLeagueIngestionUseCase:
    repository: LeagueIngestionJobRepository

    def execute(
        self, league_id: int, league_name: str, season_year: int
    ) -> LeagueIngestionJob:
        for job in self.repository.list_jobs():
            if (
                job.league_id == league_id
                and job.season_year == season_year
                and not job.is_completed
            ):
                return job

        return self.repository.save_job(
            LeagueIngestionJob(
                id=None,
                league_id=league_id,
                league_name=league_name,
                season_year=season_year,
            )
        )
