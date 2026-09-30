from datetime import date

from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics
from player_scouting.presentation.api.dependencies import get_player_repository
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import InMemoryPlayerRepository

LA_LIGA_2023 = Season("La Liga", "2023")
PREMIER_LEAGUE_2023 = Season("Premier League", "2023")
COPA_DEL_REY_1984 = Season("Copa del Rey", "1983/1984")


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


def test_list_players_returns_the_most_recent_season_year_for_each_player():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Current Player", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(2, "Historical Player", "Forward", date(1960, 1, 1)),
        COPA_DEL_REY_1984,
        Statistics(0, 0),
    )
    client = _client_with_repository(repository)

    response = client.get("/players")

    body = {player["player_id"]: player for player in response.json()}
    assert body[1]["latest_season_year"] == 2023
    assert body[2]["latest_season_year"] == 1983


def test_list_players_returns_the_highest_season_year_when_a_player_has_several():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        Season("Premier League", "2018"),
        Statistics(2, 1),
    )
    client = _client_with_repository(repository)

    response = client.get("/players")

    body = response.json()[0]
    assert body["latest_season_year"] == 2023


def test_list_players_returns_null_season_year_for_a_player_with_no_seasons():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "No Seasons", "Forward", date(1995, 1, 1)))
    client = _client_with_repository(repository)

    response = client.get("/players")

    assert response.json()[0]["latest_season_year"] is None


def _repository_with_three_scorers() -> InMemoryPlayerRepository:
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Jude Bellingham", "Midfielder", None, birth_year=2003),
        Season("La Liga", "2026"),
        Statistics(3, 9),
    )
    repository.add(
        Player(2, "Kylian Mbappe", "Forward", None, birth_year=1998),
        Season("La Liga", "2026"),
        Statistics(7, 2),
    )
    repository.add(
        Player(3, "Old Legend", "Forward", date(1960, 1, 1)),
        COPA_DEL_REY_1984,
        Statistics(40, 0),
    )
    return repository


def test_list_players_filters_by_name():
    client = _client_with_repository(_repository_with_three_scorers())

    response = client.get("/players?q=jude")

    assert [p["name"] for p in response.json()] == ["Jude Bellingham"]


def test_list_players_sorts_most_recent_first_by_default():
    client = _client_with_repository(_repository_with_three_scorers())

    response = client.get("/players")

    # Same season (2026): Bellingham 3+9 contributions beats Mbappe 7+2.
    assert [p["player_id"] for p in response.json()] == [1, 2, 3]


def test_list_players_sorts_by_goals_and_limits_the_result():
    client = _client_with_repository(_repository_with_three_scorers())

    response = client.get("/players?sort=goals&limit=2")

    assert [p["player_id"] for p in response.json()] == [3, 2]


def test_list_players_rejects_an_unknown_sort():
    client = _client_with_repository(_repository_with_three_scorers())

    response = client.get("/players?sort=height")

    assert response.status_code == 422


def test_players_with_only_a_birth_year_expose_it_and_a_null_date():
    client = _client_with_repository(_repository_with_three_scorers())

    response = client.get("/players?q=jude")

    player = response.json()[0]
    assert player["birth_year"] == 2003
    assert player["date_of_birth"] is None


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


def test_get_player_returns_its_photo_when_available():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(
            1,
            "Player One",
            "Forward",
            date(1995, 1, 1),
            photo_url="https://media.api-sports.io/football/players/1.png",
        ),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.status_code == 200
    assert (
        response.json()["photo_url"]
        == "https://media.api-sports.io/football/players/1.png"
    )


def test_get_player_returns_null_photo_when_not_available():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.json()["photo_url"] is None


def test_get_player_returns_its_preferred_foot_when_available():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1), preferred_foot="right"),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.json()["preferred_foot"] == "right"


def test_get_player_returns_null_preferred_foot_when_not_available():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1")

    assert response.json()["preferred_foot"] is None


def test_get_market_value_returns_the_history_and_the_current_value():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    repository.save_market_value_history(
        1,
        [
            MarketValuePoint(date(2019, 10, 17), 2_500_000, "Birmingham City"),
            MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid"),
        ],
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/market-value")

    assert response.status_code == 200
    body = response.json()
    assert len(body["history"]) == 2
    assert body["current"] == {
        "as_of": "2025-01-01",
        "amount_eur": 160_000_000,
        "club": "Real Madrid",
    }


def test_get_market_value_returns_null_current_when_there_is_no_history():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Player One", "Forward", date(1995, 1, 1)),
        LA_LIGA_2023,
        Statistics(10, 5),
    )
    client = _client_with_repository(repository)

    response = client.get("/players/1/market-value")

    assert response.status_code == 200
    body = response.json()
    assert body["current"] is None
    assert body["history"] == []


def test_get_market_value_returns_404_when_player_is_missing():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players/999/market-value")

    assert response.status_code == 404


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
        "team": None,
    }


def test_find_similar_players_returns_404_when_target_is_missing():
    client = _client_with_repository(InMemoryPlayerRepository())

    response = client.get("/players/1/similar")

    assert response.status_code == 404


def test_player_exposes_minutes_and_understat_metrics():
    repository = InMemoryPlayerRepository()
    repository.add(
        Player(1, "Lamine Yamal", "Forward", None, birth_year=2007),
        Season("La Liga", "2026"),
        Statistics(7, 4, minutes_played=598),
    )
    repository.save_season_advanced(
        1,
        Season("La Liga", "2026"),
        AdvancedStatistics(
            expected_goals=6.08,
            expected_assists=4.08,
            key_passes=27,
            xg_chain=9.5,
            xg_buildup=2.1,
        ),
    )
    client = _client_with_repository(repository)

    body = client.get("/players/1").json()

    assert body["minutes_played"] == 598
    assert body["expected_goals"] == 6.08
    assert body["expected_assists"] == 4.08
    assert body["key_passes"] == 27
    assert body["xg_chain"] == 9.5
    assert body["xg_buildup"] == 2.1


def test_player_seasons_include_the_team():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_season_statistics(
        1, Season("La Liga", "2026"), Statistics(7, 4), team="Barcelona"
    )
    client = _client_with_repository(repository)

    body = client.get("/players/1/seasons").json()

    assert body == [{"competition": "La Liga", "label": "2026", "team": "Barcelona"}]
