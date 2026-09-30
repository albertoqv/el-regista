from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from player_scouting.application.ports import HostingUsage

GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"

# Same prices and measurements as the official CLI (`railway usage`,
# railwayapp/cli src/commands/usage.rs): usage comes in GB-minutes / vCPU-minutes.
MINUTES_IN_MONTH = 43_200.0
PRICES = {
    "MEMORY_USAGE_GB": ("Memoria", 10.0 / MINUTES_IN_MONTH),
    "CPU_USAGE": ("CPU", 20.0 / MINUTES_IN_MONTH),
    "NETWORK_TX_GB": ("Tráfico de salida", 0.05),
    "DISK_USAGE_GB": ("Disco", 0.15 / MINUTES_IN_MONTH),
    "BACKUP_USAGE_GB": ("Backups", 0.15 / MINUTES_IN_MONTH),
}

_CONTEXT = """
query WorkspaceUsageContext($workspaceId: String!) {
  workspace(workspaceId: $workspaceId) {
    customer {
      currentUsage
      billingPeriod { start end }
      usageLimit { softLimit hardLimit isOverLimit }
    }
  }
}
"""
_USAGE = """
query WorkspaceUsage(
  $workspaceId: String!
  $measurements: [MetricMeasurement!]!
  $startDate: DateTime!
  $endDate: DateTime!
) {
  usage(
    workspaceId: $workspaceId
    measurements: $measurements
    includeDeleted: true
    startDate: $startDate
    endDate: $endDate
  ) { measurement value }
}
"""
_ESTIMATED = """
query WorkspaceEstimatedUsage(
  $workspaceId: String!
  $measurements: [MetricMeasurement!]!
) {
  estimatedUsage(
    workspaceId: $workspaceId
    measurements: $measurements
    includeDeleted: true
  ) { measurement estimatedValue }
}
"""


def _cost(values: dict[str, float]) -> dict[str, float]:
    return {
        label: values.get(measurement, 0.0) * price
        for measurement, (label, price) in PRICES.items()
    }


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class RailwayUsageProvider:
    """What the API server costs this month, read from Railway's public API."""

    def __init__(
        self, http_client: httpx.Client, token: str, workspace_id: str
    ) -> None:
        self._http_client = http_client
        self._token = token
        self._workspace_id = workspace_id

    def current_usage(self) -> HostingUsage:
        customer = self._query(_CONTEXT, {})["workspace"]["customer"]
        period = customer["billingPeriod"]
        measured = {
            row["measurement"]: float(row["value"])
            for row in self._query(
                _USAGE,
                {
                    "measurements": list(PRICES),
                    "startDate": period["start"],
                    "endDate": period["end"],
                },
            )["usage"]
        }
        line_items = _cost(measured)
        metered = sum(line_items.values())
        current = float(customer.get("currentUsage") or metered)
        try:
            estimated_values = {
                row["measurement"]: float(row["estimatedValue"])
                for row in self._query(
                    _ESTIMATED, {"measurements": list(PRICES)}
                )["estimatedUsage"]
            }
            # Like the CLI: projected metered usage plus any non-metered charges.
            estimated: float | None = sum(_cost(estimated_values).values()) + max(
                current - metered, 0.0
            )
        except (RuntimeError, httpx.HTTPError):
            estimated = None
        limit = customer.get("usageLimit") or {}
        return HostingUsage(
            period_start=_datetime(period["start"]),
            period_end=_datetime(period["end"]),
            current_dollars=current,
            estimated_dollars=estimated,
            line_items={k: v for k, v in line_items.items() if v > 0},
            usage_limit_dollars=limit.get("hardLimit") or limit.get("softLimit"),
        )

    def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self._http_client.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "variables": {"workspaceId": self._workspace_id, **variables},
            },
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=20,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise RuntimeError(body["errors"][0].get("message", "Railway API error"))
        data: dict[str, Any] = body["data"]
        return data
