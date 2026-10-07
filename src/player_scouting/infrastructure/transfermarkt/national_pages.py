"""National teams on Transfermarkt: a national team's performance page works like a
club's. Its competition selector lists every competition and season it played
(verified on Spain's page, Oct 2026), and the same page filtered by one of them
gives each player's line (read with league_pages.extract_club_season)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# <option value="UNLA&2026">UEFA Nations League A 26/27</option>; "&2026" alone is
# the season total and is skipped.
_OPTION = re.compile(
    r'<option[^>]*value="([A-Z0-9]+)&(?:amp;)?(\d{4})"[^>]*>\s*([^<]+?)\s*</option>'
)
_SEASON_SUFFIX = re.compile(r"\s+\d{2,4}/\d{2}$")

# Finals tournaments are known by the year they are played: the summer (or winter)
# after the season starts (World Cup 25/26 = 2026). Codes seen on Spain's and
# Argentina's pages and in the public dataset (Oct 2026).
_TOURNAMENTS = {
    "FIWC": "Mundial",
    "EURO": "Eurocopa",
    "COPA": "Copa América",
    "AFCN": "Copa África",
    "AFAC": "Copa Asia",
    "CONC": "Copa Confederaciones",
}
_NAMES = {
    "UNLA": "Nations League A",
    "UNLB": "Nations League B",
    "UNLC": "Nations League C",
    "UNLD": "Nations League D",
    "UNFI": "Nations League (fase final)",
    "EMQ": "Clasificación Eurocopa",
    "POEM": "Clasificación Eurocopa (repesca)",
    "POWM": "Clasificación Mundial (repesca)",
    "FS": "Amistosos",
    "AFT": "Finalissima",
}


@dataclass(frozen=True)
class CompetitionOption:
    code: str
    season: int
    name: str


def extract_competition_options(html: str) -> list[CompetitionOption]:
    return [
        CompetitionOption(code, int(season), _SEASON_SUFFIX.sub("", name))
        for code, season, name in _OPTION.findall(html)
    ]


def national_line_label(option: CompetitionOption) -> tuple[str, str]:
    """(name shown on the page, season label) of a national team competition."""
    if option.code in _TOURNAMENTS:
        return _TOURNAMENTS[option.code], str(option.season + 1)
    if option.code.startswith("WMQ"):
        # One code per confederation (WMQ6 = Europe): all are World Cup qualifiers.
        return "Clasificación Mundial", str(option.season)
    return _NAMES.get(option.code, option.name), str(option.season)
