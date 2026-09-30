"""Looks players up on Transfermarkt from this machine and sends the results to the API.

Transfermarkt throttles the API's own IP (Railway) after ~130 players, so the
lookups run elsewhere: a developer machine or a GitHub Actions runner.

    export API_BASE_URL=... INGESTION_API_KEY=...
    uv run python scripts/enrich_remote.py --limit 300
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import time
from collections.abc import Callable

import httpx

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.provider import (
    TransfermarktMarketValueProvider,
)

PAUSE_SECONDS = 1.5
PAGE_SIZE = 50
RETRIES = 6
RETRY_PAUSE_SECONDS = 20


def _call(send: Callable[[], httpx.Response]) -> httpx.Response:
    """Retries API calls through a redeploy (502/503) or a network blip."""
    for attempt in range(RETRIES):
        try:
            response = send()
            if response.status_code < 500:
                response.raise_for_status()
                return response
        except httpx.TransportError:
            pass
        if attempt < RETRIES - 1:
            time.sleep(RETRY_PAUSE_SECONDS)
    response = send()
    response.raise_for_status()
    return response


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=125)
    args = parser.parse_args()
    # Windows consoles use a legacy codepage: never die over a name like "Modrić".
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    api = httpx.Client(
        base_url=os.environ["API_BASE_URL"],
        headers={"X-Ingestion-Key": os.environ["INGESTION_API_KEY"]},
        timeout=60,
    )
    provider = TransfermarktMarketValueProvider(
        TransfermarktClient(http_client=httpx.Client(timeout=30))
    )

    found = missing = 0
    while found + missing < args.limit:
        size = min(PAGE_SIZE, args.limit - found - missing)
        pending = _call(
            lambda: api.get("/ingestion/enrichment/pending", params={"limit": size})
        )
        players = pending.json()
        if not players:
            break
        for player in players:
            try:
                result = provider.get_market_value_history(
                    player["name"], player["birth_year"]
                )
            except EnrichmentUnavailableError as error:
                print(f"Transfermarkt is not answering, stopping: {error}")
                print(f"found={found} not_found={missing}")
                return 0
            body: dict[str, object] = {"found": result is not None}
            if result is not None:
                body |= {
                    "photo_url": result.photo_url,
                    "date_of_birth": (
                        result.date_of_birth.isoformat()
                        if result.date_of_birth
                        else None
                    ),
                    "preferred_foot": result.preferred_foot,
                    "market_values": [
                        {
                            "as_of": point.as_of.isoformat(),
                            "amount_eur": point.amount_eur,
                            "club": point.club,
                        }
                        for point in result.points
                    ],
                }
                found += 1
            else:
                missing += 1
            url = f"/ingestion/enrichment/{player['player_id']}"
            _call(lambda: api.post(url, json=body))
            status = "ok" if result else "not found"
            print(f"{found + missing:4d} {player['name']}: {status}", flush=True)
            time.sleep(PAUSE_SECONDS)

    print(f"found={found} not_found={missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
