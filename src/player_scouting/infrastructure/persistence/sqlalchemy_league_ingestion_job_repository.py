from __future__ import annotations

from sqlalchemy.orm import Session

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.infrastructure.persistence.models import LeagueIngestionJobModel


class SqlAlchemyLeagueIngestionJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_job(self, job: LeagueIngestionJob) -> LeagueIngestionJob:
        model = (
            self._session.get(LeagueIngestionJobModel, job.id)
            if job.id is not None
            else None
        )
        if model is None:
            model = LeagueIngestionJobModel()
            self._session.add(model)
        model.league_id = job.league_id
        model.league_name = job.league_name
        model.season_year = job.season_year
        model.next_page = job.next_page
        model.total_pages = job.total_pages
        self._session.flush()
        return self._to_domain(model)

    def get_job(self, job_id: int) -> LeagueIngestionJob | None:
        model = self._session.get(LeagueIngestionJobModel, job_id)
        if model is None:
            return None
        return self._to_domain(model)

    def list_jobs(self) -> list[LeagueIngestionJob]:
        models = self._session.query(LeagueIngestionJobModel).order_by(
            LeagueIngestionJobModel.id
        )
        return [self._to_domain(model) for model in models]

    def next_pending_job(self) -> LeagueIngestionJob | None:
        for job in self.list_jobs():
            if not job.is_completed:
                return job
        return None

    @staticmethod
    def _to_domain(model: LeagueIngestionJobModel) -> LeagueIngestionJob:
        return LeagueIngestionJob(
            id=model.id,
            league_id=model.league_id,
            league_name=model.league_name,
            season_year=model.season_year,
            next_page=model.next_page,
            total_pages=model.total_pages,
        )
