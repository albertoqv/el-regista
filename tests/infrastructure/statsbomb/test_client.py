import httpx
import pytest

from player_scouting.infrastructure.statsbomb.client import StatsBombClient

BASE_URL = "https://example-statsbomb.test/data"


def _client_with_handler(handler) -> StatsBombClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return StatsBombClient(http_client=http_client, base_url=BASE_URL)


def test_get_matches_requests_the_expected_url_and_returns_the_json_body():
    requested_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, json=[{"match_id": 1}])

    client = _client_with_handler(handler)

    matches = client.get_matches(competition_id=43, season_id=3)

    assert matches == [{"match_id": 1}]
    assert requested_urls == [f"{BASE_URL}/matches/43/3.json"]


def test_get_lineups_requests_the_expected_url_and_returns_the_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{BASE_URL}/lineups/7.json"
        return httpx.Response(200, json=[{"team_id": 1, "lineup": []}])

    client = _client_with_handler(handler)

    lineups = client.get_lineups(match_id=7)

    assert lineups == [{"team_id": 1, "lineup": []}]


def test_get_events_requests_the_expected_url_and_returns_the_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{BASE_URL}/events/7.json"
        return httpx.Response(200, json=[{"id": "abc"}])

    client = _client_with_handler(handler)

    events = client.get_events(match_id=7)

    assert events == [{"id": "abc"}]


def test_raises_for_a_non_success_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = _client_with_handler(handler)

    with pytest.raises(httpx.HTTPStatusError):
        client.get_matches(competition_id=999, season_id=999)
