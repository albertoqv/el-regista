from player_scouting.presentation.api.read_cache import ReadCache, cached_reads


class CountingRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def list_season_records(self, labels):
        self.calls.append(("list_season_records", tuple(labels)))
        return [f"record {label}" for label in labels]

    def get_player(self, player_id):
        self.calls.append(("get_player", (player_id,)))
        return f"player {player_id}"


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _cached(clock=None):
    inner = CountingRepository()
    cache = ReadCache(ttl_seconds=60, clock=clock or Clock())
    return inner, cache, cached_reads(inner, cache, {"list_season_records"})


def test_a_bulk_read_with_the_same_arguments_reaches_the_database_once():
    inner, _, repository = _cached()

    first = repository.list_season_records(["2026"])
    second = repository.list_season_records(["2026"])

    assert first == second == ["record 2026"]
    assert len(inner.calls) == 1


def test_other_arguments_are_read_again():
    inner, _, repository = _cached()

    repository.list_season_records(["2026"])
    repository.list_season_records(["2025", "2026"])

    assert len(inner.calls) == 2


def test_other_methods_are_not_cached():
    inner, _, repository = _cached()

    repository.get_player(7)
    repository.get_player(7)

    assert len(inner.calls) == 2


def test_callers_cannot_change_what_is_cached():
    _, _, repository = _cached()

    repository.list_season_records(["2026"]).append("intruder")

    assert repository.list_season_records(["2026"]) == ["record 2026"]


def test_reads_expire_and_can_be_cleared():
    clock = Clock()
    inner, cache, repository = _cached(clock)

    repository.list_season_records(["2026"])
    clock.now = 61
    repository.list_season_records(["2026"])
    cache.clear()
    repository.list_season_records(["2026"])

    assert len(inner.calls) == 3


def test_any_ingestion_empties_the_bulk_reads():
    from fastapi.testclient import TestClient

    from player_scouting.presentation.api.main import create_app
    from player_scouting.presentation.api.read_cache import READ_CACHE

    READ_CACHE.get_or_load("players", lambda: ["old"])
    # Whatever the ingestion answers (here: no such route), the cache is emptied.
    TestClient(create_app()).post("/ingestion/no-such-step")

    assert READ_CACHE.get_or_load("players", lambda: ["new"]) == ["new"]


def test_calls_with_keyword_arguments_are_not_cached():
    # Time windows ("from now on") change on every call: caching them fills memory.
    inner, _, repository = _cached()

    repository.list_season_records(labels=["2026"])
    repository.list_season_records(labels=["2026"])

    assert len(inner.calls) == 2


def test_the_cache_keeps_a_bounded_number_of_reads():
    inner = CountingRepository()
    cache = ReadCache(ttl_seconds=60, clock=Clock(), max_entries=2)
    repository = cached_reads(inner, cache, {"list_season_records"})

    for label in ("2024", "2025", "2026", "2024"):
        repository.list_season_records([label])

    assert len(inner.calls) == 4
