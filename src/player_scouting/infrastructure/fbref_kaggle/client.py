from __future__ import annotations

import io
import zipfile

import httpx

DATASET_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "hubertsidorowicz/football-players-stats-{start}-{end}"
)
LIGHT_FILE_NAME = "players_data_light-{start}_{end}.csv"


class FbrefKaggleClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def download_season_csv(self, start_year: int) -> str:
        end_year = start_year + 1
        response = self._http_client.get(
            DATASET_URL.format(start=start_year, end=end_year),
            follow_redirects=True,
            timeout=120,
        )
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            raw = archive.read(LIGHT_FILE_NAME.format(start=start_year, end=end_year))
        return raw.decode("utf-8-sig")
