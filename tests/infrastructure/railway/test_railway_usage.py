import json
from datetime import datetime, timezone

import httpx
import pytest

from player_scouting.infrastructure.railway.provider import RailwayUsageProvider

# Real responses from backboard.railway.com (30 Sep 2026), same queries as the
# official CLI's `railway usage`.
CONTEXT = {
    "data": {
        "workspace": {
            "customer": {
                "currentUsage": 0.13774788749308642,
                "billingPeriod": {
                    "start": "2026-09-29T11:22:57.647Z",
                    "end": "2026-09-30T23:59:59.999Z",
                },
                "usageLimit": None,
            }
        }
    }
}
USAGE = {
    "data": {
        "usage": [
            {"measurement": "MEMORY_USAGE_GB", "value": 548.2126131882667},
            {"measurement": "CPU_USAGE", "value": 20.692373366666665},
            {"measurement": "NETWORK_TX_GB", "value": 0.019704097},
            {"measurement": "DISK_USAGE_GB", "value": 234.9361152},
            {"measurement": "BACKUP_USAGE_GB", "value": 0},
        ]
    }
}
ESTIMATED = {
    "data": {
        "estimatedUsage": [
            {"measurement": "MEMORY_USAGE_GB", "estimatedValue": 640.3423782580759},
            {"measurement": "CPU_USAGE", "estimatedValue": 24.259555022087312},
            {"measurement": "NETWORK_TX_GB", "estimatedValue": 0.02311188052545017},
            {"measurement": "DISK_USAGE_GB", "estimatedValue": 275.56783879087675},
            {"measurement": "BACKUP_USAGE_GB", "estimatedValue": 0},
        ]
    }
}


def _provider(responses, seen=None):
    def handler(request):
        body = json.loads(request.content)
        if seen is not None:
            seen.append((request.headers.get("authorization"), body))
        query = body["query"]
        if "estimatedUsage" in query:
            return httpx.Response(200, json=ESTIMATED)
        if "usage(" in query:
            return httpx.Response(200, json=USAGE)
        return httpx.Response(200, json=responses)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return RailwayUsageProvider(client, token="tok", workspace_id="ws-1")


def test_reads_the_bill_like_the_railway_cli():
    seen = []
    usage = _provider(CONTEXT, seen).current_usage()

    assert usage.current_dollars == pytest.approx(0.1377, abs=1e-4)
    assert usage.period_start == datetime(2026, 9, 29, 11, 22, 57, 647000, timezone.utc)
    # The CLI printed 0.1616 for this same data.
    assert usage.estimated_dollars == pytest.approx(0.1616, abs=1e-3)
    assert usage.line_items["Memoria"] == pytest.approx(0.1269, abs=1e-4)
    assert usage.line_items["CPU"] == pytest.approx(0.0096, abs=1e-4)
    assert "Backups" not in usage.line_items
    assert usage.usage_limit_dollars is None
    assert {auth for auth, _ in seen} == {"Bearer tok"}
    assert seen[0][1]["variables"]["workspaceId"] == "ws-1"
    for _, body in seen[1:]:
        assert "MEMORY_USAGE_GB" in body["variables"]["measurements"]


def test_graphql_errors_are_raised_with_their_message():
    def handler(request):
        return httpx.Response(200, json={"errors": [{"message": "Not Authorized"}]})

    provider = RailwayUsageProvider(
        httpx.Client(transport=httpx.MockTransport(handler)), "bad", "ws"
    )

    with pytest.raises(RuntimeError, match="Not Authorized"):
        provider.current_usage()
