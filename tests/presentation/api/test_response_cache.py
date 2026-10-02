from datetime import date

from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.presentation.api.dependencies import (
    get_player_repository,
    get_shot_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.response_cache import ResponseCache
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings
from tests.application.doubles import InMemoryPlayerRepository, InMemoryShotRepository


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_an_entry_expires_after_its_time_to_live():
    clock = Clock()
    cache = ResponseCache(ttl_seconds=60, max_bytes=1000, clock=clock)
    cache.put("/players", b"[]", "application/json")

    clock.now = 59
    assert cache.get("/players") == (b"[]", "application/json")
    clock.now = 61
    assert cache.get("/players") is None


def test_the_least_recently_used_entries_leave_when_memory_runs_out():
    cache = ResponseCache(ttl_seconds=60, max_bytes=10, clock=Clock())
    cache.put("/a", b"aaaa", "application/json")
    cache.put("/b", b"bbbb", "application/json")
    cache.get("/a")
    cache.put("/c", b"cccc", "application/json")

    assert cache.get("/a") is not None
    assert cache.get("/b") is None
    assert cache.get("/c") is not None


def test_a_response_bigger_than_the_whole_cache_is_not_kept():
    cache = ResponseCache(ttl_seconds=60, max_bytes=10, clock=Clock())
    cache.put("/big", b"x" * 11, "application/json")

    assert cache.get("/big") is None


class CountingRepository(InMemoryPlayerRepository):
    def __init__(self) -> None:
        super().__init__()
        self.searches = 0

    def search_player_summaries(self, *args, **kwargs):
        self.searches += 1
        return super().search_player_summaries(*args, **kwargs)


def _client(repository):
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: repository
    app.dependency_overrides[get_shot_repository] = InMemoryShotRepository
    app.dependency_overrides[get_api_settings] = lambda: ApiSettings(
        ingestion_api_key=""
    )
    return TestClient(app)


def _repository():
    repository = CountingRepository()
    repository.add(
        Player(1, "Pedri", "Midfielder", date(2002, 11, 25)),
        Season("La Liga", "2026"),
        Statistics(2, 3),
    )
    return repository


def test_a_repeated_question_is_answered_from_memory():
    repository = _repository()
    client = _client(repository)

    first = client.get("/players?q=pedri")
    second = client.get("/players?q=pedri")

    assert repository.searches == 1
    assert second.json() == first.json()
    assert (first.headers["x-cache"], second.headers["x-cache"]) == ("MISS", "HIT")


def test_new_data_empties_the_cache():
    repository = _repository()
    client = _client(repository)
    client.get("/players?q=pedri")

    client.post("/ingestion/maintenance/merge-duplicates")
    client.get("/players?q=pedri")

    assert repository.searches == 2


def test_private_and_live_endpoints_are_never_cached():
    client = _client(_repository())

    client.get("/health")
    response = client.get("/health")

    assert "x-cache" not in response.headers
