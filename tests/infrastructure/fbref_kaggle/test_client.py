import io
import zipfile

import httpx
import pytest

from player_scouting.infrastructure.fbref_kaggle.client import FbrefKaggleClient

CSV_TEXT = "Rk,Player,Comp\n1,Jude Bellingham,es La Liga\n"


def _zip_with(file_name: str, content: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(file_name, content)
        archive.writestr("players_data-2026_2027.csv", "full,version\n")
    return buffer.getvalue()


def test_downloads_the_season_zip_and_returns_the_light_csv():
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(
            200, content=_zip_with("players_data_light-2026_2027.csv", CSV_TEXT)
        )

    client = FbrefKaggleClient(httpx.Client(transport=httpx.MockTransport(handler)))

    text = client.download_season_csv(2026)

    assert text == CSV_TEXT
    assert requested == [
        "https://www.kaggle.com/api/v1/datasets/download/"
        "hubertsidorowicz/football-players-stats-2026-2027"
    ]


def test_follows_the_redirect_kaggle_answers_with():
    def handler(request: httpx.Request) -> httpx.Response:
        if "kaggle.com" in str(request.url):
            return httpx.Response(
                302, headers={"Location": "https://storage.example.test/file.zip"}
            )
        return httpx.Response(
            200, content=_zip_with("players_data_light-2026_2027.csv", CSV_TEXT)
        )

    client = FbrefKaggleClient(httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.download_season_csv(2026) == CSV_TEXT


def test_raises_for_a_season_that_does_not_exist():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = FbrefKaggleClient(httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(httpx.HTTPStatusError):
        client.download_season_csv(1990)
