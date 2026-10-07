"""Reads national teams' competitions on Transfermarkt (Nations League, qualifiers,
World Cup, Euro, Copa América, friendlies...) and sends each player's lines to the API.

The national teams are those of the last World Cup and Euro. Finished competitions
never change, so they are read once and remembered in .cache/national-teams.json;
the ones in progress are read again at most once a week. Each run reads at most
--pages pages, so the first backfill spreads over several runs instead of asking
Transfermarkt for hundreds of pages at once. Runs at home (scripts/home_sync.ps1).

    export API_BASE_URL=... INGESTION_API_KEY=...
    uv run python scripts/scrape_national_teams_remote.py
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import httpx

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.league_pages import (
    ClubLink,
    TransfermarktLeagueScraper,
)
from player_scouting.infrastructure.transfermarkt.national_pages import (
    CompetitionOption,
    extract_competition_options,
    national_line_label,
)

STATE = Path(".cache/national-teams.json")
# Participants pages of the last finals tournaments (slugs and editions verified on
# Transfermarkt, Oct 2026): World Cup 2026 (season 25/26) and Euro 2024 (23/24).
TOURNAMENTS = (("world-cup", "FIWC", 2025), ("europameisterschaft", "EURO", 2023))
# Seasons read: the last World Cup cycle and the current one.
SINCE = 2022


def _current_season() -> int:
    today = date.today()
    return today.year if today.month >= 7 else today.year - 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=150)
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    done: set[str] = set(state.get("done", []))
    last_current = state.get("current_read_on", "2000-01-01")
    read_current = date.fromisoformat(last_current) <= date.today() - timedelta(days=6)
    current = _current_season()

    api = httpx.Client(
        base_url=os.environ["API_BASE_URL"],
        headers={"X-Ingestion-Key": os.environ["INGESTION_API_KEY"].strip()},
        timeout=120,
    )
    scraper = TransfermarktLeagueScraper(
        TransfermarktClient(http_client=httpx.Client(timeout=30))
    )
    budget = args.pages
    try:
        teams: dict[int, ClubLink] = {}
        for slug, code, season in TOURNAMENTS:
            for team in scraper.participants(slug, code, season):
                teams.setdefault(team.club_id, team)
            budget -= 1
        for team in teams.values():
            if budget <= 0:
                break
            # A team's list of competitions changes only with new fixtures: kept in
            # the state file and read again once a week.
            known = state.setdefault("options", {})
            if str(team.club_id) not in known or read_current:
                known[str(team.club_id)] = [
                    [option.code, option.season, option.name]
                    for option in extract_competition_options(
                        scraper.performance_page(team)
                    )
                    if option.season >= SINCE
                ]
                budget -= 1
            options = [
                CompetitionOption(code, season, name)
                for code, season, name in known[str(team.club_id)]
            ]
            for option in options:
                key = f"{team.club_id}|{option.code}|{option.season}"
                in_progress = option.season >= current - 1
                if (key in done and not in_progress) or (
                    in_progress and not read_current
                ):
                    continue
                if budget <= 0:
                    break
                lines = scraper.club_lines([team], option.code, option.season)
                budget -= 1
                name, label = national_line_label(option)
                rows = [
                    {
                        "transfermarkt_id": line.transfermarkt_id,
                        "team": team.name,
                        "appearances": line.appearances,
                        "goals": line.goals,
                        "assists": line.assists,
                        "minutes_played": line.minutes_played,
                        "yellow_cards": line.yellow_cards,
                        "red_cards": line.red_cards,
                    }
                    for _, line in lines
                ]
                if rows:
                    api.post(
                        "/ingestion/transfermarkt/competition-lines",
                        json={
                            "competition": name,
                            "kind": "national",
                            "season_label": label,
                            "rows": rows,
                        },
                    ).raise_for_status()
                print(f"{team.name} {name} {label}: {len(rows)} lines", flush=True)
                if not in_progress:
                    done.add(key)
        else:
            if read_current:
                state["current_read_on"] = date.today().isoformat()
    except EnrichmentUnavailableError as error:
        print(f"Transfermarkt is not answering, stopping: {error}")
    finally:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        state["done"] = sorted(done)
        STATE.write_text(json.dumps(state, indent=1))
    print(f"pages left in this run's budget: {budget}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
