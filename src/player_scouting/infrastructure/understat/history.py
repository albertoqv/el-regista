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
    missing_only: bool = False,
) -> None:
    """One file per league season, then the index of each player's seasons and
    the percentile profiles. `missing_only` asks Understat only for seasons that
    have no file yet: past seasons never change."""
    out_dir.mkdir(parents=True, exist_ok=True)
    first = True
    for year in years:
        for league in leagues:
            competition = LEAGUES[league]
            if missing_only and (out_dir / f"{slug(competition)}-{year}.json").exists():
                continue
            if not first:
                time.sleep(pause_seconds)
            first = False
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
    write_profiles(out_dir)


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


# The radar axes of the history (web/lib/history.ts HISTORY_METRICS), in this order.
PROFILE_METRICS = [
    "goals",
    "expected_goals",
    "shots",
    "assists",
    "expected_assists",
    "key_passes",
    "xg_chain",
    "xg_buildup",
]
# A regular's season: below this, per-90 numbers are noise (as in the web).
REGULAR_MINUTES = 900
PROFILE_FIELDS = [
    "id",
    "name",
    "team",
    "competition",
    "year",
    "minutes",
    *PROFILE_METRICS,
    *(f"p_{metric}" for metric in PROFILE_METRICS),
]


def _per_90(player: dict[str, Any], metric: str) -> float:
    return float(player[metric]) * 90 / player["minutes"]


def build_profiles(seasons: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Every regular of every league season with his totals and his percentile in
    each metric against the regulars of his line in that league season: a few rows
    per player that twins, best seasons and peaks read without the season files.
    Goalkeepers are left out (Understat's metrics say nothing about them)."""
    competitions = sorted({season["competition"] for season in seasons})
    by_position: dict[str, list[list[Any]]] = {}
    for season in sorted(seasons, key=lambda s: (s["year"], s["competition"])):
        regulars = [
            player
            for player in season["players"]
            if player["minutes"] >= REGULAR_MINUTES
            and player["position"] != "Goalkeeper"
        ]
        for player in regulars:
            peers = [p for p in regulars if p["position"] == player["position"]]
            percentiles = []
            for metric in PROFILE_METRICS:
                mine = _per_90(player, metric)
                below = sum(1 for peer in peers if _per_90(peer, metric) <= mine)
                # Half up, like Math.round in the web.
                percentiles.append(int(below / len(peers) * 100 + 0.5))
            by_position.setdefault(player["position"], []).append(
                [
                    player["id"],
                    player["name"],
                    player["team"],
                    competitions.index(season["competition"]),
                    season["year"],
                    player["minutes"],
                    *(player[metric] for metric in PROFILE_METRICS),
                    *percentiles,
                ]
            )
    return {
        position: {
            "fields": PROFILE_FIELDS,
            "competitions": competitions,
            "rows": rows,
        }
        for position, rows in by_position.items()
    }


def write_profiles(out_dir: Path) -> None:
    """profiles/<line>.json from the season files (one file per line keeps each
    under the 2 MB the web's fetch cache takes)."""
    seasons = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(out_dir.glob("*-*.json"))
    ]
    folder = out_dir / "profiles"
    folder.mkdir(exist_ok=True)
    for position, payload in build_profiles(seasons).items():
        (folder / f"{position.lower()}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
