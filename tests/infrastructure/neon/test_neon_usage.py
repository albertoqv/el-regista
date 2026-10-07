from datetime import UTC, datetime

import httpx
import pytest

from player_scouting.infrastructure.neon.provider import (
    FREE_TRANSFER_BYTES,
    NeonUsageProvider,
)

# Shape of GET /api/v2/projects/{project_id} per Neon's API reference (Oct 2026); the
# key is personal, so this follows the documented field names, not a captured answer.
PROJECT = {
    "project": {
        "id": "neon-cerise-fountain-12345678",
        "name": "el-regista",
        "region_id": "aws-us-east-1",
        "data_transfer_bytes": 1_250_000_000,
        "written_data_bytes": 52_000_000,
        "compute_time_seconds": 86_400,
        "active_time_seconds": 345_600,
        "consumption_period_start": "2026-10-01T00:00:00Z",
        "consumption_period_end": "2026-11-01T00:00:00Z",
    }
}


def _provider(status: int, body: dict, seen: list[httpx.Request]) -> NeonUsageProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, json=body)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return NeonUsageProvider(client, "napi_test", "neon-cerise-fountain-12345678")


def test_reads_the_transfer_of_the_current_period_against_the_free_allowance():
    seen: list[httpx.Request] = []

    usage = _provider(200, PROJECT, seen).current_usage()

    assert str(seen[0].url) == (
        "https://console.neon.tech/api/v2/projects/neon-cerise-fountain-12345678"
    )
    assert seen[0].headers["Authorization"] == "Bearer napi_test"
    assert usage.transfer_bytes == 1_250_000_000
    assert usage.transfer_limit_bytes == FREE_TRANSFER_BYTES == 5_000_000_000
    assert usage.compute_seconds == 86_400
    assert usage.written_bytes == 52_000_000
    assert usage.period_start == datetime(2026, 10, 1, tzinfo=UTC)
    assert usage.period_end == datetime(2026, 11, 1, tzinfo=UTC)


def test_a_refused_key_is_an_error_the_panel_can_show():
    with pytest.raises(httpx.HTTPStatusError):
        _provider(401, {"message": "authorization failed"}, []).current_usage()
