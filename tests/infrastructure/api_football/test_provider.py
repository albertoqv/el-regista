from datetime import date

import httpx

from player_scouting.domain.season import Season
from player_scouting.infrastructure.api_football.provider import (
    ApiFootballPlayerSeasonProvider,
)

# Shape captured from a real call to https://v3.football.api-sports.io/players
# (league=140, season=2023, search=Bellingham) during this session.
BELLINGHAM_RESPONSE = {
    "response": [
        {
            "player": {
                "id": 129718,
                "name": "J. Bellingham",
                "birth": {"date": "2003-06-29"},
            },
            "statistics": [
                {
                    "team": {"id": 541, "name": "Real Madrid"},
                    "league": {"id": 140, "name": "La Liga", "season": 2023},
                    "games": {"position": "Midfielder"},
                    "shots": {"total": 49, "on": 35},
                    "goals": {"total": 19, "assists": 6},
                    "passes": {"total": 1500, "key": 48, "accuracy": 48},
                    "tackles": {"total": 43, "interceptions": 21},
                    "dribbles": {"attempts": 85, "success": 50},
                    "fouls": {"drawn": 72, "committed": 32},
                    "cards": {"yellow": 5, "yellowred": None, "red": 1},
                }
            ],
        }
    ]
}


def _provider_with(response_body: dict) -> ApiFootballPlayerSeasonProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return ApiFootballPlayerSeasonProvider(http_client=http_client, api_key="test-key")


def test_maps_a_real_shaped_response_to_a_player_season_result():
    provider = _provider_with(BELLINGHAM_RESPONSE)

    result = provider.get_player_statistics(
        "Bellingham", league_id=140, season_year=2023
    )

    assert result is not None
    assert result.player_id == 129718
    assert result.name == "J. Bellingham"
    assert result.position == "Midfielder"
    assert result.date_of_birth == date(2003, 6, 29)
    assert result.season == Season("La Liga", "2023")


def test_maps_the_statistics_block_including_derived_passes_completed():
    provider = _provider_with(BELLINGHAM_RESPONSE)

    result = provider.get_player_statistics(
        "Bellingham", league_id=140, season_year=2023
    )

    stats = result.statistics
    assert stats.goals == 19
    assert stats.assists == 6
    assert stats.shots == 49
    assert stats.shots_on_target == 35
    assert stats.passes_attempted == 1500
    assert stats.passes_completed == 720  # 1500 * 48%
    assert stats.key_passes == 48
    assert stats.dribbles_attempted == 85
    assert stats.dribbles_completed == 50
    assert stats.tackles_won == 43
    assert stats.interceptions == 21
    assert stats.fouls_committed == 32
    assert stats.fouls_won == 72
    assert stats.yellow_cards == 5
    assert stats.red_cards == 1


def test_sums_red_and_second_yellow_cards_into_red_cards():
    response = {
        "response": [
            {
                "player": {
                    "id": 1,
                    "name": "Some Player",
                    "birth": {"date": "1995-01-01"},
                },
                "statistics": [
                    {
                        "league": {"name": "Premier League", "season": 2023},
                        "games": {"position": "Defender"},
                        "shots": {},
                        "goals": {},
                        "passes": {},
                        "tackles": {},
                        "dribbles": {},
                        "fouls": {},
                        "cards": {"yellow": 0, "yellowred": 1, "red": 1},
                    }
                ],
            }
        ]
    }
    provider = _provider_with(response)

    result = provider.get_player_statistics(
        "Some Player", league_id=39, season_year=2023
    )

    assert result.statistics.red_cards == 2


def test_returns_none_when_there_are_no_results():
    provider = _provider_with({"response": []})

    result = provider.get_player_statistics("Nobody", league_id=140, season_year=2023)

    assert result is None


def test_sends_the_expected_query_params_and_api_key_header():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"response": []})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ApiFootballPlayerSeasonProvider(
        http_client=http_client, api_key="secret-key"
    )

    provider.get_player_statistics("Haaland", league_id=39, season_year=2023)

    request = captured_requests[0]
    assert request.url.params["league"] == "39"
    assert request.url.params["season"] == "2023"
    assert request.url.params["search"] == "Haaland"
    assert request.headers["x-apisports-key"] == "secret-key"
