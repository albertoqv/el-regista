"""Reads the season in progress of the big five leagues, Europe and the domestic cups
on Transfermarkt and sends each competition's lines to the API.

The public dataset only has finished seasons. Transfermarkt blocks datacenter IPs,
so this runs at home (scripts/home_sync.ps1) and only the lines travel to the API.

    export API_BASE_URL=... INGESTION_API_KEY=...
    uv run python scripts/scrape_competitions_remote.py --season 2026
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from datetime import date

import httpx

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.domain.competitions import CompetitionKind
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.league_pages import (
    BIG_FIVE_LEAGUES,
    DOMESTIC_CUPS,
    EUROPEAN_CUPS,
    ClubLink,
    ScrapedLine,
    TransfermarktLeagueScraper,
    clubs_also_in,
)


def _current_season() -> int:
    today = date.today()
    return today.year if today.month >= 7 else today.year - 1


def _send(
    api: httpx.Client,
    competition: str,
    kind: CompetitionKind,
    season: int,
    lines: list[tuple[str, ScrapedLine]],
) -> None:
    rows = [
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
    ]
    if not rows:
        print(f"{competition} {season}: no lines yet", flush=True)
        return
    response = api.post(
        "/ingestion/transfermarkt/competition-lines",
        json={
            "competition": competition,
            "kind": kind,
            "season_label": str(season),
            "rows": rows,
        },
    )
    response.raise_for_status()
    print(f"{competition} {season}: {response.json()['ingested']} lines", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=_current_season())
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    api = httpx.Client(
        base_url=os.environ["API_BASE_URL"],
        headers={"X-Ingestion-Key": os.environ["INGESTION_API_KEY"].strip()},
        timeout=120,
    )
    scraper = TransfermarktLeagueScraper(
        TransfermarktClient(http_client=httpx.Client(timeout=30))
    )
    season = args.season
    try:
        top_flights: dict[str, list[ClubLink]] = {}
        for code, name in BIG_FIVE_LEAGUES.items():
            top_flights[code] = scraper.league_clubs(code, season)
            _send(
                api,
                name,
                "league",
                season,
                scraper.club_lines(top_flights[code], code, season),
            )
        for code, (slug, name) in EUROPEAN_CUPS.items():
            clubs = scraper.participants(slug, code, season)
            _send(
                api,
                name,
                "continental",
                season,
                scraper.club_lines(clubs, code, season),
            )
        for code, (slug, name, league) in DOMESTIC_CUPS.items():
            clubs = clubs_also_in(
                scraper.participants(slug, code, season), top_flights[league]
            )
            _send(api, name, "cup", season, scraper.club_lines(clubs, code, season))
    except EnrichmentUnavailableError as error:
        # Competitions already sent are kept; the next run finishes the rest.
        print(f"Transfermarkt is not answering, stopping: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
