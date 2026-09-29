from player_scouting.application.league_ingestion_job import LeagueIngestionJob


def test_a_freshly_created_job_is_not_completed():
    job = LeagueIngestionJob(
        id=None, league_id=140, league_name="La Liga", season_year=2023
    )

    assert job.is_completed is False


def test_a_job_without_total_pages_yet_is_not_completed():
    job = LeagueIngestionJob(
        id=1, league_id=140, league_name="La Liga", season_year=2023, next_page=2
    )

    assert job.is_completed is False


def test_a_job_is_completed_once_next_page_passes_total_pages():
    job = LeagueIngestionJob(
        id=1,
        league_id=140,
        league_name="La Liga",
        season_year=2023,
        next_page=46,
        total_pages=45,
    )

    assert job.is_completed is True


def test_a_job_on_its_last_page_is_not_yet_completed():
    job = LeagueIngestionJob(
        id=1,
        league_id=140,
        league_name="La Liga",
        season_year=2023,
        next_page=45,
        total_pages=45,
    )

    assert job.is_completed is False
