from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class LeagueIngestionJob:
    id: int | None
    league_id: int
    league_name: str
    season_year: int
    next_page: int = 1
    total_pages: int | None = None

    @property
    def is_completed(self) -> bool:
        return self.total_pages is not None and self.next_page > self.total_pages


class LeagueIngestionJobRepository(Protocol):
    def save_job(self, job: LeagueIngestionJob) -> LeagueIngestionJob: ...

    def get_job(self, job_id: int) -> LeagueIngestionJob | None: ...

    def list_jobs(self) -> list[LeagueIngestionJob]: ...

    def next_pending_job(self) -> LeagueIngestionJob | None: ...
