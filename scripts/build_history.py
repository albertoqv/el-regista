"""Writes web/public/history: the big five leagues from 2014 to 2023 from Understat.

Run once (and again only to add a season); see infrastructure/understat/history.py.

    uv run python scripts/build_history.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.history import build_history
from player_scouting.infrastructure.understat.provider import LEAGUES

# 2024 on lives in the database (the seasons the refresh keeps up to date).
YEARS = list(range(2014, 2024))
OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "history"


def main() -> int:
    build_history(UnderstatClient(httpx.Client(timeout=60)), list(LEAGUES), YEARS, OUT)
    print(f"written: {len(list(OUT.glob('*.json')))} files in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
