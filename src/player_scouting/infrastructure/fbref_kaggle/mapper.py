from __future__ import annotations

import hashlib
from collections.abc import Iterable

from player_scouting.application.ports import PlayerSeasonResult
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics

# FBref rows carry no numeric player id; ids are derived into a range that cannot
# collide with StatsBomb/API-Football ids and still fits a Postgres INTEGER.
_ID_RANGE_START = 1_000_000_000
_ID_RANGE_END = 2_147_483_647

_POSITIONS = {
    "GK": "Goalkeeper",
    "DF": "Defender",
    "MF": "Midfielder",
    "FW": "Forward",
}


def player_id_for(name: str, birth_year: int | None) -> int:
    digest = hashlib.sha256(f"fbref:{name}|{birth_year}".encode()).digest()
    span = _ID_RANGE_END - _ID_RANGE_START
    return _ID_RANGE_START + int.from_bytes(digest[:8], "big") % span


def normalize_competition(comp: str) -> str:
    prefix, _, rest = comp.partition(" ")
    if rest and prefix.islower():
        return rest
    return comp


def normalize_position(pos: str) -> str | None:
    first = pos.split(",")[0].strip()
    return _POSITIONS.get(first)


def _int(row: dict[str, str], column: str) -> int:
    value = (row.get(column) or "").strip()
    return int(float(value)) if value else 0


def _float(row: dict[str, str], column: str) -> float:
    value = (row.get(column) or "").strip()
    return float(value) if value else 0.0


def _birth_year(row: dict[str, str]) -> int | None:
    value = (row.get("Born") or "").strip()
    return int(float(value)) if value else None


def _statistics(row: dict[str, str]) -> Statistics:
    return Statistics(
        goals=_int(row, "Gls"),
        assists=_int(row, "Ast"),
        shots=_int(row, "Sh"),
        shots_on_target=_int(row, "SoT"),
        expected_goals=_float(row, "xG"),
        passes_completed=_int(row, "Cmp"),
        passes_attempted=_int(row, "Att"),
        key_passes=_int(row, "KP"),
        dribbles_completed=_int(row, "Succ"),
        dribbles_attempted=_int(row, "Att_stats_possession"),
        tackles_won=_int(row, "TklW"),
        interceptions=_int(row, "Int"),
        fouls_committed=_int(row, "Fls"),
        fouls_won=_int(row, "Fld"),
        yellow_cards=_int(row, "CrdY"),
        # FBref's CrdR already counts reds that came from a second yellow.
        red_cards=_int(row, "CrdR"),
    )


def rows_to_results(
    rows: Iterable[dict[str, str]], start_year: int
) -> list[PlayerSeasonResult]:
    by_key: dict[tuple[int, str], PlayerSeasonResult] = {}
    for row in rows:
        name = (row.get("Player") or "").strip()
        if not name:
            continue
        birth_year = _birth_year(row)
        player_id = player_id_for(name, birth_year)
        season = Season(
            normalize_competition((row.get("Comp") or "").strip()), str(start_year)
        )
        statistics = _statistics(row)

        key = (player_id, season.competition)
        existing = by_key.get(key)
        if existing is not None:
            existing.statistics = existing.statistics + statistics
            continue
        by_key[key] = PlayerSeasonResult(
            player_id=player_id,
            name=name,
            position=normalize_position(row.get("Pos") or ""),
            date_of_birth=None,
            birth_year=birth_year,
            season=season,
            statistics=statistics,
        )
    return list(by_key.values())
