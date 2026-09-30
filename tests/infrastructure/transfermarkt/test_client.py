import httpx
import pytest

from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient

BASE_URL = "https://example-transfermarkt.test"


def _client_with_handler(handler) -> TransfermarktClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return TransfermarktClient(http_client=http_client, base_url=BASE_URL)


def test_search_player_requests_the_expected_url_and_returns_the_html_body():
    requested_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, text="<html>results</html>")

    client = _client_with_handler(handler)

    html = client.search_player("Jude Bellingham")

    assert html == "<html>results</html>"
    assert requested_urls == [
        f"{BASE_URL}/schnellsuche/ergebnis/schnellsuche?query=Jude+Bellingham"
    ]


def test_search_player_sends_a_browser_user_agent():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "Mozilla" in request.headers["User-Agent"]
        return httpx.Response(200, text="<html></html>")

    client = _client_with_handler(handler)

    client.search_player("Jude Bellingham")


def test_get_profile_requests_the_given_path_and_returns_the_html_body():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == f"{BASE_URL}/jude-bellingham/profil/spieler/581678"
        return httpx.Response(200, text="<html>profile</html>")

    client = _client_with_handler(handler)

    html = client.get_profile("/jude-bellingham/profil/spieler/581678")

    assert html == "<html>profile</html>"


def test_get_market_value_graph_requests_the_expected_url_and_returns_the_json_body():
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            str(request.url) == f"{BASE_URL}/ceapi/marketValueDevelopment/graph/581678"
        )
        return httpx.Response(200, json={"list": [{"y": 1}]})

    client = _client_with_handler(handler)

    data = client.get_market_value_graph(581678)

    assert data == {"list": [{"y": 1}]}


def test_raises_for_a_non_success_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = _client_with_handler(handler)

    with pytest.raises(httpx.HTTPStatusError):
        client.get_profile("/nobody/profil/spieler/0")


def test_search_without_results_returns_an_empty_page():
    # Verified live: no results redirect to /schnellsuche/keinergebnis/...
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={
                "Location": f"{BASE_URL}/schnellsuche/keinergebnis/schnellsuche?query=Lee+Kang%5C-in"
            },
        )

    client = _client_with_handler(handler)

    assert client.search_player("Lee Kang-in") == ""
