import httpx
import pytest

from player_scouting.application.ports import LeagueSummary
from player_scouting.infrastructure.api_football.league_search_provider import (
    ApiFootballLeagueSearchProvider,
)
from player_scouting.infrastructure.api_football.provider import ApiFootballError

# Shape captured from a real call to
# https://v3.football.api-sports.io/leagues?search=Serie%20A
SERIE_A_SEARCH_RESPONSE = {
    "errors": [],
    "response": [
        {
            "league": {"id": 71, "name": "Serie A", "type": "League"},
            "country": {"name": "Brazil", "code": "BR"},
        },
        {
            "league": {"id": 135, "name": "Serie A", "type": "League"},
            "country": {"name": "Italy", "code": "IT"},
        },
    ],
}


def _provider_with(response_body: dict) -> ApiFootballLeagueSearchProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response_body)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return ApiFootballLeagueSearchProvider(http_client=http_client, api_key="test-key")


def test_maps_real_shaped_search_results():
    provider = _provider_with(SERIE_A_SEARCH_RESPONSE)

    results = provider.search_leagues("Serie A")

    assert len(results) == 2
    assert results[0] == LeagueSummary(id=71, name="Serie A", country="Brazil")
    assert results[1] == LeagueSummary(id=135, name="Serie A", country="Italy")


def test_sends_the_expected_query_param_and_api_key_header():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"errors": [], "response": []})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ApiFootballLeagueSearchProvider(
        http_client=http_client, api_key="secret-key"
    )

    provider.search_leagues("Bundesliga")

    request = captured_requests[0]
    assert request.url.params["search"] == "Bundesliga"
    assert request.headers["x-apisports-key"] == "secret-key"


def test_raises_when_the_api_reports_an_error():
    provider = _provider_with(
        {"errors": {"rateLimit": "Too many requests"}, "response": []}
    )

    with pytest.raises(ApiFootballError):
        provider.search_leagues("Serie A")


def test_returns_an_empty_list_when_there_are_no_results():
    provider = _provider_with({"errors": [], "response": []})

    assert provider.search_leagues("Nonexistent League") == []
