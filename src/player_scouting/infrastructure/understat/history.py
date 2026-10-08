"""Past seasons of the big five leagues from Understat, as static files for the web.

Seasons that never change do not belong in the database: Neon's free plan meters
every byte read (5 GB a month). They are read once from Understat (one request per
league and season), written as small JSON files under web/public/history and served
by Vercel's CDN. The web reads them for radars and duels of older seasons.
"""

from __future__ import annotations

import json
import time
import unicodedata
from pathlib import Path
from typing import Any, Protocol

from player_scouting.infrastructure.understat.provider import LEAGUES

# Understat's position codes start with the line the player plays in ("F M S").
_POSITIONS = {"F": "Forward", "M": "Midfielder", "D": "Defender", "G": "Goalkeeper"}


class LeaguePlayers(Protocol):
    def get_league_players(self, league: str, season: int) -> list[dict]: ...


def slug(competition: str) -> str:
    return competition.lower().replace(" ", "-")


def history_row(raw: dict) -> dict[str, Any]:
    def number(key: str) -> float:
        return round(float(raw.get(key) or 0), 2)

    return {
        "id": int(raw["id"]),
        "name": raw["player_name"],
        # A mid-season move lists both clubs: the first is the one shown.
        "team": raw["team_title"].split(",")[0].strip(),
        "position": _POSITIONS.get(raw.get("position", "M")[:1], "Midfielder"),
        "games": int(raw["games"]),
        "minutes": int(raw["time"]),
        "goals": int(raw["goals"]),
        "expected_goals": number("xG"),
        "shots": int(raw["shots"]),
        "assists": int(raw["assists"]),
        "expected_assists": number("xA"),
        "key_passes": int(raw["key_passes"]),
        "xg_chain": number("xGChain"),
        "xg_buildup": number("xGBuildup"),
        "yellow_cards": int(raw["yellow_cards"]),
        "red_cards": int(raw["red_cards"]),
    }


def build_history(
    understat: LeaguePlayers,
    leagues: list[str],
    years: list[int],
    out_dir: Path,
    pause_seconds: float = 3.0,
) -> None:
    """One file per league season, then the index of each player's seasons."""
    out_dir.mkdir(parents=True, exist_ok=True)
    first = True
    for year in years:
        for league in leagues:
            if not first:
                time.sleep(pause_seconds)
            first = False
            competition = LEAGUES[league]
            players = [
                history_row(raw) for raw in understat.get_league_players(league, year)
            ]
            if not players:
                continue
            path = out_dir / f"{slug(competition)}-{year}.json"
            path.write_text(
                json.dumps(
                    {"competition": competition, "year": year, "players": players},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                encoding="utf-8",
            )
    write_index(out_dir)


def index_key(name: str) -> str:
    """The shard a name lives in: its first letter, without accents."""
    normalized = normalized_name(name)
    first = normalized[:1]
    return first if "a" <= first <= "z" else "_"


def normalized_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip()


def write_index(out_dir: Path) -> None:
    """index/<letter>.json: normalized name -> his seasons, from the season files.
    A lookup reads one small file instead of every player of ten years."""
    shards: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for path in sorted(out_dir.glob("*-*.json")):
        season = json.loads(path.read_text(encoding="utf-8"))
        for player in season["players"]:
            shard = shards.setdefault(index_key(player["name"]), {})
            shard.setdefault(normalized_name(player["name"]), []).append(
                {
                    "id": player["id"],
                    "name": player["name"],
                    "competition": season["competition"],
                    "year": season["year"],
                    "team": player["team"],
                }
            )
    folder = out_dir / "index"
    folder.mkdir(exist_ok=True)
    for key, shard in shards.items():
        (folder / f"{key}.json").write_text(
            json.dumps(shard, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
