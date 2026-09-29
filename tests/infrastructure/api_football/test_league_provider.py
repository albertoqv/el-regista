import httpx
import pytest

from player_scouting.infrastructure.api_football.league_provider import (
    ApiFootballLeaguePlayersProvider,
)
from player_scouting.infrastructure.api_football.provider import ApiFootballError

# Shape captured from a real call to
# https://v3.football.api-sports.io/players?league=140&season=2023&page=1
LA_LIGA_PAGE_1 = {
    "errors": [],
    "paging": {"current": 1, "total": 45},
    "response": [
        {
            "player": {
                "id": 15,
                "name": "T. Delaney",
                "birth": {"date": "1991-09-03"},
                "photo": "https://media.api-sports.io/football/players/15.png",
            },
            "statistics": [
                {
                    "league": {"id": 140, "name": "La Liga", "season": 2023},
                    "games": {"position": "Midfielder"},
                    "shots": {"total": None, "on": None},
                    "goals": {"total": None, "assists": None},
                    "passes": {"total": None, "key": None, "accuracy": None},
                    "tackles": {"total": None, "interceptions": None},
                    "dribbles": {"attempts": None, "success": None},
                    "fouls": {"drawn": None, "committed": None},
                    "cards": {"yellow": None, "yellowred": None, "red": None},
                }
            ],
        },
        {
            "player": {
                "id": 16,
                "name": "No Stats Player",
                "birth": {"date": "1990-01-01"},
            },
            "statistics": [],
        },
    ],
}


def _provider_with(response_body: dict) -> ApiFootballLeaguePlayersProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return ApiFootballLeaguePlayersProvider(http_client=http_client, api_key="test-key")


def test_maps_a_real_shaped_page_including_paging_info():
    provider = _provider_with(LA_LIGA_PAGE_1)

    page = provider.get_players_page(league_id=140, season_year=2023, page=1)

    assert page.current_page == 1
    assert page.total_pages == 45
    assert len(page.players) == 1
    assert page.players[0].player_id == 15
    assert page.players[0].name == "T. Delaney"


def test_skips_entries_without_a_statistics_block():
    provider = _provider_with(LA_LIGA_PAGE_1)

    page = provider.get_players_page(league_id=140, season_year=2023, page=1)

    assert all(player.player_id != 16 for player in page.players)


def test_sends_the_expected_query_params_and_api_key_header():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json={"errors": [], "paging": {"current": 1, "total": 1}, "response": []},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ApiFootballLeaguePlayersProvider(
        http_client=http_client, api_key="secret-key"
    )

    provider.get_players_page(league_id=140, season_year=2023, page=3)

    request = captured_requests[0]
    assert request.url.params["league"] == "140"
    assert request.url.params["season"] == "2023"
    assert request.url.params["page"] == "3"
    assert request.headers["x-apisports-key"] == "secret-key"


def test_raises_when_the_api_reports_an_error():
    provider = _provider_with(
        {"errors": {"rateLimit": "Too many requests"}, "paging": {}, "response": []}
    )

    with pytest.raises(ApiFootballError):
        provider.get_players_page(league_id=140, season_year=2023, page=1)


def test_skips_entries_with_missing_or_invalid_birth_date_instead_of_failing():
    response = {
        "errors": [],
        "paging": {"current": 1, "total": 1},
        "response": [
            {
                "player": {"id": 99, "name": "No Birth Date", "birth": {"date": None}},
                "statistics": [
                    {
                        "league": {"name": "La Liga", "season": 2023},
                        "games": {"position": "Forward"},
                        "shots": {},
                        "goals": {},
                        "passes": {},
                        "tackles": {},
                        "dribbles": {},
                        "fouls": {},
                        "cards": {},
                    }
                ],
            }
        ],
    }
    provider = _provider_with(response)

    page = provider.get_players_page(league_id=140, season_year=2023, page=1)

    assert page.players == []
