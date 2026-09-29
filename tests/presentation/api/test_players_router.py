from datetime import date

from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.presentation.api.dependencies import get_player_repository
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import InMemoryPlayerRepository

LA_LIGA_2023 = Season("La Liga", "2023")
PREMIER_LEAGUE_2023 = Season("Premier League", "2023")


def _client_with_repository(repository: InMemoryPlayerRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: repository
    return TestClient(app)


def test_list_players_returns_every_player():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(2, "Player Two", "Midfielder", date(1996, 1, 1)),
        LA_LIGA_2023,
        Statistics(3, 3),
    )
    client = _client_with_repository(repository)

    response = client.get("/players")

    assert response.status_code == 200
    body = response.json()
    assert {player["player_id"] for player in body} == {1, 2}


def test_list_players_returns_an_empty_list_when_there_are_no_players():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players")

    assert response.status_code == 200
    assert response.json() == []


def test_get_player_returns_its_career_statistics():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        PREMIER_LEAGUE_2023,
        Statistics(2, 1),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Player One"
    assert body["goals"] == 12
    assert body["assists"] == 6


def test_get_player_returns_its_extended_metrics():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5, shots=20, expected_goals=6.7, yellow_cards=2),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.status_code == 200
    body = response.json()
    assert body["shots"] == 20
    assert body["expected_goals"] == 6.7
    assert body["yellow_cards"] == 2


def test_get_player_returns_404_when_player_is_missing():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players/999")

    assert response.status_code == 404


def test_list_seasons_returns_every_season_a_player_has_statistics_for():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        PREMIER_LEAGUE_2023,
        Statistics(2, 1),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/seasons")

    assert response.status_code == 200
    body = response.json()
    assert {(s["competition"], s["label"]) for s in body} == {
        ("La Liga", "2023"),
        ("Premier League", "2023"),
    }


def test_get_season_statistics_returns_that_seasons_numbers():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        PREMIER_LEAGUE_2023,
        Statistics(2, 1),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/seasons/La Liga/2023")

    assert response.status_code == 200
    body = response.json()
    assert body["goals"] == 10
    assert body["assists"] == 5


def test_get_season_statistics_returns_404_for_an_unknown_season():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/seasons/Bundesliga/2023")

    assert response.status_code == 404


def test_compare_players_returns_the_similarity_percentage_using_career_totals():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 15),
    )
    repository.add(
        Player(2, "Player Two", "Forward", date(1996, 1, 1)),
        PREMIER_LEAGUE_2023,
        Statistics(15, 10),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/compare/2")

    assert response.status_code == 200
    body = response.json()
    assert body["similarity_percentage"] == 67
    assert body["player1"]["player_id"] == 1
    assert body["player2"]["player_id"] == 2


def test_compare_players_returns_404_when_a_player_is_missing():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players/1/compare/2")

    assert response.status_code == 404


def test_find_similar_players_returns_ranked_matches_with_their_season():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Target", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 10),
    )
    repository.add(
        Player(2, "Close", "Forward", date(1996, 1, 1)),
        PREMIER_LEAGUE_2023,
        Statistics(10, 9),
    )
    repository.add(
        Player(3, "Far", "Forward", date(1997, 1, 1)), LA_LIGA_2023, Statistics(1, 1)
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/similar?top=1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["comparison"]["player2"]["player_id"] == 2
    assert body[0]["candidate_season"] == {
        "competition": "Premier League",
        "label": "2023",
    }


def test_find_similar_players_returns_404_when_target_is_missing():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players/1/similar")

    assert response.status_code == 404
