from __future__ import annotations

import tempfile
from pathlib import Path

import httpx

# Public Kaggle dataset built from Transfermarkt (verified: downloads without an
# account, ~250 MB zip, refreshed periodically).
DATASET_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/davidcariboo/player-scores"
)
CHUNK_BYTES = 1 << 20


class TransfermarktDatasetClient:
    def __init__(self, http_client: httpx.Client) -> None:
        self._http_client = http_client

    def download_archive(self) -> Path:
        """Streams the zip to a temporary file so it never sits in memory."""
        target = Path(tempfile.gettempdir()) / "transfermarkt-dataset.zip"
        with self._http_client.stream(
            "GET", DATASET_URL, follow_redirects=True, timeout=600
        ) as response:
            response.raise_for_status()
            with target.open("wb") as file:
                for chunk in response.iter_bytes(CHUNK_BYTES):
                    file.write(chunk)
        return target
