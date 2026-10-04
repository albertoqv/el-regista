"""A league's season in progress from Transfermarkt's league and club pages.

The public dataset stops at the last finished season, so the extra leagues are
read here: the league table gives the clubs, and each club's performance page
(`leistungsdaten`, "plus" view) gives every player's games, goals, assists,
cards and minutes. Paths verified against live pages (Oct 2026).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup, Tag

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt_dataset.mapper import OTHER_LEAGUES

# The leagues read from club pages: the dataset's nine with player lines, its
# August-to-May top flights without them, and second divisions. Codes read off
# Transfermarkt's country pages (Oct 2026). Calendar-year leagues (Brazil, MLS,
# Scandinavia...) are left out: their seasons do not fit "2026 = 26/27".
SEASON_LEAGUES = {
    **{
        code: OTHER_LEAGUES[code]
        for code in (
            "PO1",
            "NL1",
            "TR1",
            "BE1",
            "SC1",
            "GR1",
            "DK1",
            "UKR1",
            "RU1",
            "A1",
            "C1",
            "PL1",
            "TS1",
            "KR1",
            "RO1",
            "SER1",
            "SA1",
            "MEX1",
            "AUS1",
        )
    },
    "GB2": "Championship",
    "GB3": "League One",
    "ES2": "Segunda División",
    "IT2": "Serie B",
    "L2": "2. Bundesliga",
    "L3": "3. Liga",
    "FR2": "Ligue 2",
    "NL2": "Eerste Divisie",
    "PO2": "Liga Portugal 2",
}

CLUB_LINK = re.compile(r"^/([^/]+)/startseite/verein/(\d+)/saison_id/\d+$")
PROFILE_LINK = re.compile(r"/profil/spieler/(\d+)")
# After the shirt number, player and age columns: these come in this order.
STAT_COLUMNS = (
    "in_squad",
    "appearances",
    "goals",
    "assists",
    "yellow_cards",
    "second_yellow_cards",
    "red_cards",
    "substituted_on",
    "substituted_off",
    "points_per_game",
    "minutes_played",
)
PAUSE_SECONDS = 2.0
# A slow page is tried again before giving up on the run.
ATTEMPTS = 3
RETRY_PAUSE_SECONDS = 10.0


@dataclass(frozen=True)
class ClubLink:
    name: str
    slug: str
    club_id: int


@dataclass(frozen=True)
class ScrapedLine:
    transfermarkt_id: int
    name: str
    position: str
    detailed_position: str | None
    appearances: int
    goals: int
    assists: int
    yellow_cards: int
    red_cards: int
    minutes_played: int


def _position(detailed: str) -> str:
    """Transfermarkt's detailed role -> the app's four positions."""
    if detailed == "Goalkeeper":
        return "Goalkeeper"
    if "Back" in detailed:
        return "Defender"
    if "Midfield" in detailed:
        return "Midfielder"
    return "Forward"


def _number(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def extract_league_clubs(league_html: str) -> list[ClubLink]:
    table = BeautifulSoup(league_html, "html.parser").select_one("table.items")
    if table is None:
        return []
    clubs = []
    for link in table.select("td.hauptlink a[href]"):
        match = CLUB_LINK.match(str(link["href"]))
        if match:
            clubs.append(ClubLink(link.get_text(strip=True), match[1], int(match[2])))
    return clubs


def _line(row: Tag) -> ScrapedLine | None:
    cells = row.find_all("td", recursive=False)
    link = row.select_one("td.hauptlink a[href]")
    if link is None or len(cells) < 4 + len(STAT_COLUMNS):
        return None
    # "Not used during this season" spans the stat columns.
    if any(cell.get("colspan") not in (None, "1") for cell in cells):
        return None
    profile = PROFILE_LINK.search(str(link["href"]))
    if profile is None:
        return None
    inline_rows = row.select("table.inline-table tr")
    detailed = inline_rows[-1].get_text(strip=True) if len(inline_rows) > 1 else ""
    values = {
        name: cells[4 + index].get_text(strip=True)
        for index, name in enumerate(STAT_COLUMNS)
    }
    return ScrapedLine(
        transfermarkt_id=int(profile[1]),
        name=str(link.get("title") or link.get_text(strip=True)),
        position=_position(detailed),
        detailed_position=detailed or None,
        appearances=_number(values["appearances"]),
        goals=_number(values["goals"]),
        assists=_number(values["assists"]),
        yellow_cards=_number(values["yellow_cards"]),
        red_cards=_number(values["second_yellow_cards"]) + _number(values["red_cards"]),
        minutes_played=_number(values["minutes_played"]),
    )


def extract_club_season(club_html: str) -> list[ScrapedLine]:
    table = BeautifulSoup(club_html, "html.parser").select_one("table.items")
    if table is None:
        return []
    lines = [_line(row) for row in table.select(":scope > tbody > tr")]
    return [line for line in lines if line is not None and line.appearances > 0]


class TransfermarktLeagueScraper:
    def __init__(
        self,
        client: TransfermarktClient,
        pause_seconds: float = PAUSE_SECONDS,
        retry_pause_seconds: float = RETRY_PAUSE_SECONDS,
    ) -> None:
        self._client = client
        self._pause = pause_seconds
        self._retry_pause = retry_pause_seconds

    def league_season(
        self, competition_code: str, start_year: int
    ) -> list[tuple[str, ScrapedLine]]:
        """(club, line) for every player who has played; stops if blocked."""
        clubs = extract_league_clubs(
            self._page(
                f"/wettbewerb/startseite/wettbewerb/{competition_code}"
                f"/saison_id/{start_year}"
            )
        )
        rows: list[tuple[str, ScrapedLine]] = []
        for club in clubs:
            time.sleep(self._pause)
            html = self._page(
                f"/{club.slug}/leistungsdaten/verein/{club.club_id}"
                f"/reldata/{competition_code}%26{start_year}/plus/1"
            )
            rows.extend((club.name, line) for line in extract_club_season(html))
        return rows

    def _page(self, path: str) -> str:
        for attempt in range(ATTEMPTS):
            try:
                return self._client.get_page(path)
            except httpx.HTTPStatusError as error:
                if error.response.status_code in (403, 429):
                    raise EnrichmentUnavailableError(str(error)) from error
                raise
            except httpx.TransportError as error:
                # Timeouts and dropped connections: wait and retry, then stop the run
                # (leagues already sent are kept) instead of crashing it.
                if attempt == ATTEMPTS - 1:
                    raise EnrichmentUnavailableError(str(error)) from error
                time.sleep(self._retry_pause)
        raise AssertionError("unreachable")
