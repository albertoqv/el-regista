"""Vercel entrypoint: the FastAPI app, served as a Vercel Function.

Vercel looks for an `app` in a root index.py; the code lives in src/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from player_scouting.presentation.api.main import app  # noqa: E402

__all__ = ["app"]
