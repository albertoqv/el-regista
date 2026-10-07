"""The database's consumption this month, from Neon's API (GET project).

The Free plan allows 5 GB of public network transfer a month; past it, Neon may
suspend the database until the next month (it happened in Oct 2026). The admin
panel shows how close the month is. Needs NEON_API_KEY and NEON_PROJECT_ID.
"""

from __future__ import annotations

from datetime import datetime

import httpx

from player_scouting.application.ports import DatabaseUsage

API_URL = "https://console.neon.tech/api/v2"
FREE_TRANSFER_BYTES = 5_000_000_000


class NeonUsageProvider:
    def __init__(self, client: httpx.Client, api_key: str, project_id: str) -> None:
        self._client = client
        self._api_key = api_key
        self._project_id = project_id

    def current_usage(self) -> DatabaseUsage:
        response = self._client.get(
            f"{API_URL}/projects/{self._project_id}",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10,
        )
        response.raise_for_status()
        project = response.json()["project"]
        return DatabaseUsage(
            period_start=datetime.fromisoformat(project["consumption_period_start"]),
            period_end=datetime.fromisoformat(project["consumption_period_end"]),
            transfer_bytes=int(project["data_transfer_bytes"]),
            transfer_limit_bytes=FREE_TRANSFER_BYTES,
            compute_seconds=int(project["compute_time_seconds"]),
            written_bytes=int(project["written_data_bytes"]),
        )
