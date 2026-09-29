from datetime import date

from player_scouting.application.league_ingestion_job import LeagueIngestionJob
from player_scouting.application.ports import (
    LeaguePageUnavailableError,
    LeaguePlayersPage,
    PlayerSeasonResult,
)
from player_scouting.application.use_cases.process_league_ingestion_batch import (
    ProcessLeagueIngestionBatchUseCase,
)
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import (
    FakeLeaguePlayersProvider,
    InMemoryLeagueIngestionJobRepository,
    InMemoryPlayerRepository,
)

LA_LIGA_2023 = Season("La Liga", "2023")


def _player_result(player_id: int, name: str) -> PlayerSeasonResult:
    return PlayerSeasonResult(
        player_id=player_id,
        name=name,
        position="Forward",
        date_of_birth=date(1995, 1, 1),
        season=LA_LIGA_2023,
        statistics=Statistics(1, 1),
    )


def test_processes_one_page_per_request_of_budget():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job = job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    provider = FakeLeaguePlayersProvider(
        {
            (140, 2023): [
                LeaguePlayersPage(
                    players=[_player_result(1, "Player One")],
                    current_page=1,
                    total_pages=2,
                ),
                LeaguePlayersPage(
                    players=[_player_result(2, "Player Two")],
                    current_page=2,
                    total_pages=2,
                ),
            ]
        }
    )
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )

    summary = use_case.execute(request_budget=1)

    assert summary.pages_processed == 1
    assert summary.players_ingested == 1
    assert player_repository.get_player(1) is not None
    assert player_repository.get_player(2) is None
    updated_job = job_repository.get_job(job.id)
    assert updated_job.next_page == 2
    assert updated_job.total_pages == 2
    assert updated_job.is_completed is False


def test_continues_where_a_previous_batch_left_off():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    provider = FakeLeaguePlayersProvider(
        {
            (140, 2023): [
                LeaguePlayersPage([_player_result(1, "Player One")], 1, 2),
                LeaguePlayersPage([_player_result(2, "Player Two")], 2, 2),
            ]
        }
    )
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )
    use_case.execute(request_budget=1)

    summary = use_case.execute(request_budget=1)

    assert summary.pages_processed == 1
    assert player_repository.get_player(2) is not None
    assert provider.requested_pages == [(140, 2023, 1), (140, 2023, 2)]
    job = job_repository.list_jobs()[0]
    assert job.is_completed is True


def test_moves_on_to_the_next_job_once_one_completes():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    job_repository.save_job(
        LeagueIngestionJob(
            id=None,
            league_id=39,
            league_name="Premier League",
            season_year=2023,
        )
    )
    provider = FakeLeaguePlayersProvider(
        {
            (140, 2023): [LeaguePlayersPage([_player_result(1, "Player One")], 1, 1)],
            (39, 2023): [LeaguePlayersPage([_player_result(2, "Player Two")], 1, 1)],
        }
    )
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )

    summary = use_case.execute(request_budget=2)

    assert summary.pages_processed == 2
    assert player_repository.get_player(1) is not None
    assert player_repository.get_player(2) is not None
    assert all(job.is_completed for job in job_repository.list_jobs())


def test_stops_when_there_are_no_pending_jobs_even_under_budget():
    job_repository = InMemoryLeagueIngestionJobRepository()
    provider = FakeLeaguePlayersProvider({})
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )

    summary = use_case.execute(request_budget=90)

    assert summary.pages_processed == 0
    assert summary.players_ingested == 0


class _PageLimitedProvider:
    """Simulates API-Football's free-tier cap: only pages 1-3 are servable."""

    def __init__(self) -> None:
        self.requested_pages: list[int] = []

    def get_players_page(
        self, league_id: int, season_year: int, page: int
    ) -> LeaguePlayersPage:
        self.requested_pages.append(page)
        if page > 3:
            raise LeaguePageUnavailableError("page limit exceeded on this plan")
        return LeaguePlayersPage(
            players=[_player_result(page, f"Player {page}")],
            current_page=page,
            total_pages=45,
        )


def test_completes_a_job_gracefully_when_the_provider_cannot_serve_a_page():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    job_repository.save_job(
        LeagueIngestionJob(
            id=None,
            league_id=39,
            league_name="Premier League",
            season_year=2023,
        )
    )
    provider = _PageLimitedProvider()
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )

    summary = use_case.execute(request_budget=90)

    assert summary.players_ingested == 6
    jobs = job_repository.list_jobs()
    assert all(job.is_completed for job in jobs)
    la_liga_job = next(job for job in jobs if job.league_id == 140)
    assert la_liga_job.total_pages == 3


def test_a_failed_page_attempt_still_counts_against_the_request_budget():
    job_repository = InMemoryLeagueIngestionJobRepository()
    job_repository.save_job(
        LeagueIngestionJob(
            id=None, league_id=140, league_name="La Liga", season_year=2023
        )
    )
    provider = _PageLimitedProvider()
    player_repository = InMemoryPlayerRepository()
    use_case = ProcessLeagueIngestionBatchUseCase(
        provider, player_repository, job_repository
    )

    summary = use_case.execute(request_budget=4)

    assert summary.pages_processed == 4
    assert provider.requested_pages == [1, 2, 3, 4]
