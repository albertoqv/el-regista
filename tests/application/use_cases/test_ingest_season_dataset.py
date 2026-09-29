from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.application.use_cases.ingest_season_dataset import (
    IngestSeasonDatasetUseCase,
)
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import (
    FakeSeasonDatasetProvider,
    InMemoryPlayerRepository,
)

LA_LIGA_2026 = Season("La Liga", "2026")


def _result(player_id: int, name: str, goals: int) -> PlayerSeasonResult:
    return PlayerSeasonResult(
        player_id=player_id,
        name=name,
        position="Midfielder",
        date_of_birth=None,
        birth_year=2003,
        season=LA_LIGA_2026,
        statistics=Statistics(goals, 1),
    )


def test_ingests_every_player_of_the_season():
    provider = FakeSeasonDatasetProvider(
        {2026: [_result(1, "Jude Bellingham", 3), _result(2, "Pedri", 1)]}
    )
    repository = InMemoryPlayerRepository()
    use_case = IngestSeasonDatasetUseCase(provider, repository)

    result = use_case.execute(2026)

    assert result.ingested == 2
    assert repository.get_player(1).name == "Jude Bellingham"
    assert repository.get_player(1).birth_year == 2003
    assert repository.get_player(1).date_of_birth is None
    assert repository.get_season_statistics(1, LA_LIGA_2026).goals == 3


def test_re_ingesting_updates_the_season_totals_instead_of_duplicating():
    repository = InMemoryPlayerRepository()
    IngestSeasonDatasetUseCase(
        FakeSeasonDatasetProvider({2026: [_result(1, "Jude Bellingham", 3)]}),
        repository,
    ).execute(2026)

    IngestSeasonDatasetUseCase(
        FakeSeasonDatasetProvider({2026: [_result(1, "Jude Bellingham", 5)]}),
        repository,
    ).execute(2026)

    assert len(repository.list_players()) == 1
    assert repository.get_season_statistics(1, LA_LIGA_2026).goals == 5


def test_keeps_the_existing_photo_and_foot_of_an_already_enriched_player():
    repository = InMemoryPlayerRepository()
    use_case = IngestSeasonDatasetUseCase(
        FakeSeasonDatasetProvider({2026: [_result(1, "Jude Bellingham", 3)]}),
        repository,
    )
    use_case.execute(2026)
    enriched = repository.get_player(1)
    enriched.photo_url = "https://example.com/jude.png"
    enriched.preferred_foot = "right"
    repository.save_player(enriched)

    use_case.execute(2026)

    player = repository.get_player(1)
    assert player.photo_url == "https://example.com/jude.png"
    assert player.preferred_foot == "right"


def test_stores_the_team_of_each_player_season():
    result = _result(1, "Jude Bellingham", 3)
    result.team = "Real Madrid"
    repository = InMemoryPlayerRepository()

    IngestSeasonDatasetUseCase(
        FakeSeasonDatasetProvider({2026: [result]}), repository
    ).execute(2026)

    [entry] = repository.list_season_entries(LA_LIGA_2026)
    assert entry.team == "Real Madrid"
