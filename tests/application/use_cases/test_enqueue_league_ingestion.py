from player_scouting.application.use_cases.enqueue_league_ingestion import (
    EnqueueLeagueIngestionUseCase,
)
from tests.application.doubles import InMemoryLeagueIngestionJobRepository


def test_creates_a_new_job_for_a_league_and_season():
    repository = InMemoryLeagueIngestionJobRepository()
    use_case = EnqueueLeagueIngestionUseCase(repository)

    job = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)

    assert job.id is not None
    assert job.league_id == 140
    assert job.league_name == "La Liga"
    assert job.season_year == 2023
    assert job.next_page == 1
    assert job.total_pages is None


def test_is_idempotent_for_the_same_league_and_season():
    repository = InMemoryLeagueIngestionJobRepository()
    use_case = EnqueueLeagueIngestionUseCase(repository)

    first = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)
    second = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)

    assert first.id == second.id
    assert len(repository.list_jobs()) == 1


def test_allows_a_new_job_once_the_previous_one_for_that_league_is_completed():
    repository = InMemoryLeagueIngestionJobRepository()
    use_case = EnqueueLeagueIngestionUseCase(repository)
    first = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)
    repository.save_job(
        type(first)(
            id=first.id,
            league_id=first.league_id,
            league_name=first.league_name,
            season_year=first.season_year,
            next_page=2,
            total_pages=1,
        )
    )

    second = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)

    assert second.id != first.id
    assert len(repository.list_jobs()) == 2


def test_a_different_season_gets_its_own_job():
    repository = InMemoryLeagueIngestionJobRepository()
    use_case = EnqueueLeagueIngestionUseCase(repository)

    job_2023 = use_case.execute(league_id=140, league_name="La Liga", season_year=2023)
    job_2024 = use_case.execute(league_id=140, league_name="La Liga", season_year=2024)

    assert job_2023.id != job_2024.id
