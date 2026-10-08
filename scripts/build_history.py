"""Writes web/public/history: the finished seasons of the big five from Understat.

Only seasons without a file are read (past seasons never change); the index and the
percentile profiles are rebuilt from all of them (infrastructure/understat/history.py).

    uv run python scripts/build_history.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.history import build_history
from player_scouting.infrastructure.understat.provider import LEAGUES

# Finished seasons only: the one being played lives in the database.
YEARS = list(range(2014, 2026))
OUT = Path(__file__).resolve().parent.parent / "web" / "public" / "history"


def main() -> int:
    build_history(
        UnderstatClient(httpx.Client(timeout=60)),
        list(LEAGUES),
        YEARS,
        OUT,
        missing_only=True,
    )
    print(f"written: {len(list(OUT.glob('*.json')))} files in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
