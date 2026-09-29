"""Triggers one batch of the league ingestion queue against a running API.

Meant to run on a daily schedule (see the `ingestion-worker` Railway service)
so that bulk league ingestion respects API-Football's free-tier daily request
limit by spreading it over several days instead of exhausting it at once.
"""

from __future__ import annotations

import os
import sys

import httpx

DEFAULT_BUDGET = 90


def main() -> int:
    api_base_url = os.environ.get("API_BASE_URL")
    if not api_base_url:
        print("API_BASE_URL is not set", file=sys.stderr)
        return 1

    budget = int(os.environ.get("INGESTION_DAILY_BUDGET", DEFAULT_BUDGET))
    response = httpx.post(
        f"{api_base_url}/ingestion/leagues/process",
        params={"budget": budget},
        timeout=120,
    )
    response.raise_for_status()
    print(response.json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
