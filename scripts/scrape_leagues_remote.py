"""Reads the extra leagues' season in progress on Transfermarkt and sends it to the API.

The public dataset stops at the last finished season. Transfermarkt throttles the
API's own IP (Railway), so the pages are read from this machine (a developer's or
a GitHub Actions runner) and only the lines travel to the API.

    export API_BASE_URL=... INGESTION_API_KEY=...
    uv run python scripts/scrape_leagues_remote.py --season 2026
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from datetime import date

import httpx

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.league_pages import (
    SEASON_LEAGUES,
    TransfermarktLeagueScraper,
)


def _current_season() -> int:
    today = date.today()
    return today.year if today.month >= 7 else today.year - 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=_current_season())
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="also the previous season, for leagues the API does not have it for",
    )
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    api = httpx.Client(
        base_url=os.environ["API_BASE_URL"],
        headers={"X-Ingestion-Key": os.environ["INGESTION_API_KEY"]},
        timeout=120,
    )
    scraper = TransfermarktLeagueScraper(
        TransfermarktClient(http_client=httpx.Client(timeout=30))
    )
    jobs = [
        (code, competition, args.season) for code, competition in SEASON_LEAGUES.items()
    ]
    if args.backfill:
        previous = args.season - 1
        for code, competition in SEASON_LEAGUES.items():
            known = api.get(
                f"/seasons/{previous}/leaders",
                params={"competition": competition, "limit": 1},
            )
            if known.status_code == 200 and not known.json():
                jobs.append((code, competition, previous))
    for code, competition, season in jobs:
        try:
            lines = scraper.league_season(code, season)
        except EnrichmentUnavailableError as error:
            # Leagues already sent are kept; the next run finishes the rest.
            print(f"Transfermarkt is not answering, stopping: {error}")
            return 0
        rows = [
            {
                "transfermarkt_id": line.transfermarkt_id,
                "name": line.name,
                "position": line.position,
                "detailed_position": line.detailed_position,
                "team": club,
                "goals": line.goals,
                "assists": line.assists,
                "minutes_played": line.minutes_played,
                "yellow_cards": line.yellow_cards,
                "red_cards": line.red_cards,
            }
            for club, line in lines
        ]
        if not rows:
            print(f"{competition} {season}: no lines (season not started?)")
            continue
        response = api.post(
            "/ingestion/transfermarkt/league-seasons",
            json={
                "competition": competition,
                "season_label": str(season),
                "rows": rows,
            },
        )
        response.raise_for_status()
        print(
            f"{competition} {season}: {response.json()['ingested']} players", flush=True
        )
        # The same lines, with games played, for the player's page per competition.
        api.post(
            "/ingestion/transfermarkt/competition-lines",
            json={
                "competition": competition,
                "kind": "league",
                "season_label": str(season),
                "rows": [
                    {
                        "transfermarkt_id": line.transfermarkt_id,
                        "team": club,
                        "appearances": line.appearances,
                        "goals": line.goals,
                        "assists": line.assists,
                        "minutes_played": line.minutes_played,
                        "yellow_cards": line.yellow_cards,
                        "red_cards": line.red_cards,
                    }
                    for club, line in lines
                ],
            },
        ).raise_for_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
