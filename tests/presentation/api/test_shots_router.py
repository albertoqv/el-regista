from datetime import date

from fastapi.testclient import TestClient

from player_scouting.application.ports import (
    MatchRef,
    Partnership,
    PlayerShot,
    ShotLeader,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.shots import Shot
from player_scouting.presentation.api.dependencies import (
    get_shot_pause,
    get_shot_provider,
    get_shot_repository,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import FakeShotProvider, InMemoryShotRepository

RAPHINHA = Player(1, "Raphinha", "Forward", None, birth_year=1996)
YAMAL = Player(2, "Lamine Yamal", "Forward", None, birth_year=2007)
SHOT = Shot(
    shot_id=9,
    match_id=1,
    understat_player_id=101,
    player_name="Raphinha",
    minute=88,
    result="Goal",
    x=0.91,
    y=0.45,
    xg=0.35,
    situation="OpenPlay",
    shot_type="LeftFoot",
    home=True,
    assisted_by="Lamine Yamal",
    decisive=True,
)


class StubShotRepository(InMemoryShotRepository):
    def __init__(self) -> None:
        super().__init__()
        self.leader_calls: list[tuple] = []

    def list_shot_leaders(self, season_label, metric, limit, competition=None):
        self.leader_calls.append((season_label, metric, limit, competition))
        return [ShotLeader(RAPHINHA, "La Liga", "Barcelona", 3.0, 12, 40)]

    def list_player_shots(self, player_id, season_label=None):
        return [
            PlayerShot(
                SHOT, "La Liga", "2026", "Barcelona", "Getafe", date(2026, 8, 15)
            )
        ]

    def list_partnerships(self, season_label, limit, competition=None):
        return [Partnership(RAPHINHA, "Lamine Yamal", YAMAL, "Barcelona", "La Liga", 4)]


def _client(repository, provider=None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_shot_repository] = lambda: repository
    if provider is not None:
        app.dependency_overrides[get_shot_provider] = lambda: provider
        app.dependency_overrides[get_shot_pause] = lambda: lambda seconds: None
    return TestClient(app)


def test_shot_leaders_by_metric():
    repository = StubShotRepository()

    response = _client(repository).get(
        "/seasons/2026/shot-leaders?metric=late_goals&limit=5&competition=La Liga"
    )

    assert response.status_code == 200
    [leader] = response.json()
    assert (leader["name"], leader["team"], leader["value"]) == (
        "Raphinha",
        "Barcelona",
        3.0,
    )
    assert (leader["goals"], leader["shots"]) == (12, 40)
    assert repository.leader_calls == [("2026", "late_goals", 5, "La Liga")]


def test_shot_leaders_reject_an_unknown_metric():
    response = _client(StubShotRepository()).get("/seasons/2026/shot-leaders?metric=x")

    assert response.status_code == 422


def test_partnerships():
    [pair] = _client(StubShotRepository()).get("/seasons/2026/partnerships").json()

    assert pair["scorer"]["name"] == "Raphinha"
    assert pair["assister_name"] == "Lamine Yamal"
    assert pair["assister"]["player_id"] == 2
    assert pair["goals"] == 4


def test_player_shots():
    [shot] = (
        _client(StubShotRepository()).get("/players/1/shots?season_label=2026").json()
    )

    assert shot["minute"] == 88
    assert shot["result"] == "Goal"
    assert shot["decisive"] is True
    assert (shot["x"], shot["y"], shot["xg"]) == (0.91, 0.45, 0.35)
    assert (shot["team"], shot["opponent"]) == ("Barcelona", "Getafe")
    assert shot["played_on"] == "2026-08-15"


def test_ingest_shots_in_batches():
    repository = InMemoryShotRepository()
    provider = FakeShotProvider(
        matches=[
            MatchRef(1, "La Liga", "2026", date(2026, 8, 15), "Barcelona", "Getafe")
        ],
        shots={1: [SHOT]},
    )

    response = _client(repository, provider).post(
        "/ingestion/understat/shots/2026?limit=10"
    )

    assert response.status_code == 200
    assert response.json() == {"matches": 1, "shots": 1, "remaining": 0}
