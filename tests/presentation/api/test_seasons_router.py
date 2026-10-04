from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.presentation.api.dependencies import get_player_repository
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import InMemoryPlayerRepository


def _client(repository: InMemoryPlayerRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: repository
    return TestClient(app)


def _repository() -> InMemoryPlayerRepository:
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_season_statistics(
        1,
        Season("La Liga", "2026"),
        Statistics(7, 4, minutes_played=579),
        team="Barcelona",
    )
    repository.save_player(Player(2, "Harry Kane", "Forward", None, birth_year=1993))
    repository.save_season_statistics(
        2,
        Season("Bundesliga", "2026"),
        Statistics(12, 2, minutes_played=630),
        team="Bayern Munich",
    )
    return repository


def test_season_leaders_by_goals():
    client = _client(_repository())

    response = client.get("/seasons/2026/leaders?metric=goals&limit=5")

    assert response.status_code == 200
    body = response.json()
    assert [leader["name"] for leader in body] == ["Harry Kane", "Lamine Yamal"]
    assert body[0]["team"] == "Bayern Munich"
    assert body[0]["competition"] == "Bundesliga"
    assert body[0]["season_label"] == "2026"
    assert body[0]["goals"] == 12


def test_season_leaders_filtered_by_competition():
    client = _client(_repository())

    response = client.get("/seasons/2026/leaders?metric=assists&competition=La Liga")

    assert [leader["name"] for leader in response.json()] == ["Lamine Yamal"]


def test_season_leaders_reject_an_unknown_metric():
    client = _client(_repository())

    response = client.get("/seasons/2026/leaders?metric=height")

    assert response.status_code == 422


def test_player_season_percentiles():
    client = _client(_repository())

    response = client.get("/players/1/seasons/La Liga/2026/percentiles")

    assert response.status_code == 200
    body = response.json()
    assert body["position"] == "Forward"
    assert body["peer_count"] == 1
    assert body["metrics"]["goals"]["percentile"] == 50


def test_player_season_percentiles_for_an_unknown_season_is_404():
    client = _client(_repository())

    response = client.get("/players/1/seasons/La Liga/1999/percentiles")

    assert response.status_code == 404


def test_without_a_league_the_leaders_are_from_the_big_five_only():
    repository = _repository()
    repository.save_player(Player(3, "Samuel Essende", "Forward", None))
    repository.save_season_statistics(
        3, Season("Swiss Super League", "2026"), Statistics(20, 1), team="Young Boys"
    )

    names = [p["name"] for p in _client(repository).get("/seasons/2026/leaders").json()]
    swiss = _client(repository).get(
        "/seasons/2026/leaders?competition=Swiss%20Super%20League"
    )

    assert "Samuel Essende" not in names
    assert [p["name"] for p in swiss.json()] == ["Samuel Essende"]
