"""Research (Oct 2026): does betting the best available price against the consensus's
fair odds (bookmaker average or Pinnacle, margin removed) make money?

Answer on 15,145 matches of 14 leagues, 23/24-25/26 (football-data.co.uk, free):
no. 1X2 loses 8-54% at every edge threshold; over/under 2.5 is noise (tens of
bets, signs flip between seasons). The "errors" in the maximum odds are mostly
prices nobody can actually bet. So El Regista does not sell value bets.

    uv run python scripts/research_odds_value.py
"""

import csv
import io
import time

import httpx

LEAGUES = [
    "E0",
    "SP1",
    "D1",
    "I1",
    "F1",
    "N1",
    "P1",
    "B1",
    "T1",
    "E1",
    "SP2",
    "I2",
    "D2",
    "F2",
]
SEASONS = ["2324", "2425", "2526"]
EDGES = [0.0, 0.02, 0.04, 0.06, 0.10]


def f(row, key):
    try:
        value = float(row.get(key) or "")
        return value if value > 1 else None
    except ValueError:
        return None


rows = []
client = httpx.Client(timeout=30, follow_redirects=True)
for season in SEASONS:
    for league in LEAGUES:
        text = client.get(
            f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
        ).content.decode("utf-8-sig", "replace")
        for row in csv.DictReader(io.StringIO(text)):
            if row.get("FTR"):
                row["_season"] = season
                rows.append(row)
        time.sleep(0.3)
print(len(rows), "partidos")

MARKETS = [
    (
        "1X2",
        [
            ("H", "MaxH", "AvgH", "PSH", "AvgCH"),
            ("D", "MaxD", "AvgD", "PSD", "AvgCD"),
            ("A", "MaxA", "AvgA", "PSA", "AvgCA"),
        ],
    ),
    (
        "OU",
        [
            ("O", "Max>2.5", "Avg>2.5", "P>2.5", "AvgC>2.5"),
            ("U", "Max<2.5", "Avg<2.5", "P<2.5", "AvgC<2.5"),
        ],
    ),
]


def won(row, outcome):
    if outcome in "HDA":
        return row["FTR"] == outcome
    goals = int(row["FTHG"]) + int(row["FTAG"])
    return goals > 2 if outcome == "O" else goals <= 2


for reference in ("avg", "pinnacle"):
    print(f"\n== justa = {reference}")
    for market, outcomes in MARKETS:
        for edge in EDGES:
            by_season = {}
            clv = []
            for row in rows:
                best = [f(row, o[1]) for o in outcomes]
                ref = [f(row, o[2] if reference == "avg" else o[3]) for o in outcomes]
                if None in best or None in ref:
                    continue
                total = sum(1 / r for r in ref)
                for (outcome, *_cols), price, r in zip(
                    outcomes, best, ref, strict=True
                ):
                    p = (1 / r) / total
                    if price * p - 1 > edge:
                        stats = by_season.setdefault(row["_season"], [0, 0.0])
                        stats[0] += 1
                        stats[1] += (price - 1) if won(row, outcome) else -1
                        closing = f(row, _cols[3])
                        if closing:
                            clv.append(price / closing - 1)
            parts = [
                f"{s}: {n} ap., ROI {profit / n:+.1%}"
                for s, (n, profit) in sorted(by_season.items())
                if n
            ]
            beat = sum(1 for c in clv if c > 0) / len(clv) if clv else 0
            print(
                f"{market} edge>{edge:.0%}: "
                + " | ".join(parts)
                + f" | bate al cierre {beat:.0%}"
            )
