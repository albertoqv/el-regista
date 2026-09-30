from __future__ import annotations

from datetime import datetime

from player_scouting.application.ports import MatchStats

# football-data.co.uk division codes -> competition names used across the app.
# Verified in mmz4281/2526 and 2627 (Sept 2026).
LEAGUES = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
    "P1": "Liga Portugal",
    "N1": "Eredivisie",
    "B1": "Jupiler Pro League",
    "T1": "Süper Lig",
    "SC0": "Scottish Premiership",
    "G1": "Greek Super League",
}


def _int(row: dict[str, str], key: str) -> int | None:
    value = (row.get(key) or "").strip()
    return int(float(value)) if value else None


def _float(row: dict[str, str], *keys: str) -> float | None:
    """First non-empty column: closing odds first, pre-match average otherwise."""
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return float(value)
    return None


def _date(value: str):
    for layout in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, layout).date()
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {value}")


def to_match_stats(
    row: dict[str, str], competition: str, season_label: str
) -> MatchStats:
    return MatchStats(
        competition=competition,
        season_label=season_label,
        played_on=_date(row["Date"]),
        home_team=row["HomeTeam"].strip(),
        away_team=row["AwayTeam"].strip(),
        referee=(row.get("Referee") or "").strip() or None,
        home_goals=_int(row, "FTHG"),
        away_goals=_int(row, "FTAG"),
        home_goals_ht=_int(row, "HTHG"),
        away_goals_ht=_int(row, "HTAG"),
        home_shots=_int(row, "HS"),
        away_shots=_int(row, "AS"),
        home_shots_on_target=_int(row, "HST"),
        away_shots_on_target=_int(row, "AST"),
        home_fouls=_int(row, "HF"),
        away_fouls=_int(row, "AF"),
        home_corners=_int(row, "HC"),
        away_corners=_int(row, "AC"),
        home_yellows=_int(row, "HY"),
        away_yellows=_int(row, "AY"),
        home_reds=_int(row, "HR"),
        away_reds=_int(row, "AR"),
        odds_home=_float(row, "AvgCH", "AvgH"),
        odds_draw=_float(row, "AvgCD", "AvgD"),
        odds_away=_float(row, "AvgCA", "AvgA"),
        odds_over_2_5=_float(row, "AvgC>2.5", "Avg>2.5"),
        odds_under_2_5=_float(row, "AvgC<2.5", "Avg<2.5"),
    )
