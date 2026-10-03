"""Model lab: walk-forward experiments on the 1X2 model, resumable and cached.

Tune on 24/25 ("2024"), validate on 25/26 ("2025"), exactly as BacktestUseCase:
each match is forecast only with matches played before it. A change ships only
if it improves both seasons and the 25/26 gain survives a paired bootstrap.

Runs against its own database (scouting_lab) so the test suite, which empties
`scouting`, never wipes the data. Every variant's expected goals are written to
.cache/model_lab/ as soon as they are computed: a killed run resumes where it
stopped and nothing is downloaded or recomputed twice.

    uv run python scripts/model_lab.py prepare     # migrate + load Understat once
    uv run python scripts/model_lab.py run all     # or: rho calibration halflife ...
    uv run python scripts/model_lab.py report

Long runs that must survive the terminal: scripts/model_lab_background.ps1.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

LAB_URL = os.environ.get(
    "LAB_DATABASE_URL",
    "postgresql+psycopg://scouting:scouting@localhost:5433/scouting_lab",
)
# The app's settings read DATABASE_URL at import: point them at the lab first.
os.environ["DATABASE_URL"] = LAB_URL

import httpx
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from player_scouting.application.use_cases.team_analytics import (
    IngestTeamSeasonUseCase,
    _record,
)
from player_scouting.domain import prediction as P
from player_scouting.infrastructure.persistence.models import FixtureModel
from player_scouting.infrastructure.persistence.sqlalchemy_team_repository import (
    SqlAlchemyTeamRepository,
)
from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.team_provider import (
    UnderstatTeamProvider,
)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "model_lab"
RESULTS = CACHE / "results.json"
# History for the tuning season starts a season earlier (promoted teams, decay).
SEASONS = ("2022", "2023", "2024", "2025", "2026")
TUNE, VALIDATE = "2024", "2025"
MINIMUM_HISTORY = 30
SHIP_CONFIDENCE = 0.95

Rows = list[list[Any]]  # [match_id, season, competition, rate_home, rate_away, outcome]


# --- data ------------------------------------------------------------------


def prepare() -> None:
    """Migrations + Understat team seasons, only the seasons the lab lacks."""
    subprocess.run(["alembic", "upgrade", "head"], cwd=ROOT, check=True)
    engine = create_engine(LAB_URL)
    with Session(engine) as session:
        present = dict(
            session.execute(
                select(FixtureModel.season_label, func.count()).group_by(
                    FixtureModel.season_label
                )
            ).all()
        )
        provider = UnderstatTeamProvider(UnderstatClient(httpx.Client(timeout=60)))
        for season in SEASONS:
            # The current season keeps growing: always refresh it, never the rest.
            if present.get(season) and season != SEASONS[-1]:
                print(f"{season}: {present[season]} fixtures already here")
                continue
            summary = IngestTeamSeasonUseCase(
                provider, SqlAlchemyTeamRepository(session)
            ).execute(int(season))
            session.commit()
            print(f"{season}: loaded {summary}")


class Lab:
    def __init__(self) -> None:
        repository = SqlAlchemyTeamRepository(Session(create_engine(LAB_URL)))
        self.history = repository.list_team_matches(list(SEASONS[:-1]))
        self.fixtures = [
            f
            for f in repository.list_fixtures(None)
            if f.played and f.season_label in (TUNE, VALIDATE)
        ]
        if not self.fixtures:
            sys.exit("The lab is empty: run `model_lab.py prepare` first.")
        self.teams = defaultdict(set)
        for match in self.history:
            self.teams[(match.competition, match.season_label)].add(match.team)
        last = max(f.kickoff for f in self.fixtures)
        self.fingerprint = f"{len(self.history)}-{len(self.fixtures)}-{last:%Y%m%d}"

    # --- walk-forward expected goals, cached per variant ---------------------

    def rows(self, name: str, ratings: Callable[..., P.LeagueRatings]) -> Rows:
        key = hashlib.sha1(f"{name}|{self.fingerprint}".encode()).hexdigest()[:12]
        path = CACHE / f"xg-{name}-{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        print(f"computing {name}...", flush=True)
        out: Rows = []
        by_league = defaultdict(list)
        for fixture in self.fixtures:
            by_league[fixture.competition].append(fixture)
        for league, fixtures in by_league.items():
            league_history = [m for m in self.history if m.competition == league]
            cache: dict[Any, P.LeagueRatings] = {}
            for f in fixtures:
                day = f.kickoff.date()
                earlier = [m for m in league_history if m.played_on < day]
                if len({m.match_id for m in earlier}) < MINIMUM_HISTORY:
                    continue
                if day not in cache:
                    cache[day] = ratings([_record(m) for m in earlier], day, league, f)
                r = cache[day]
                rh = r.home_goals * r.attack_of(f.home_team) * r.defence_of(f.away_team)
                ra = r.away_goals * r.attack_of(f.away_team) * r.defence_of(f.home_team)
                result = (
                    0
                    if f.home_goals > f.away_goals
                    else 1
                    if f.home_goals == f.away_goals
                    else 2
                )
                out.append([f.match_id, f.season_label, league, rh, ra, result])
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out))
        return out

    def promoted(self, league: str, fixture: Any) -> set[str]:
        previous = self.teams[(league, str(int(fixture.season_label) - 1))]
        return self.teams[(league, fixture.season_label)] - previous


# --- scoring -----------------------------------------------------------------


def probabilities(rh: float, ra: float, rho: float, power: float) -> list[float]:
    matrix = P.score_matrix(rh, ra, rho)
    n = P.MAX_GOALS + 1
    home = sum(matrix[h][a] for h in range(n) for a in range(n) if h > a)
    draw = sum(matrix[h][a] for h in range(n) for a in range(n) if h == a)
    p = [home, draw, 1 - home - draw]
    if power != 1.0:
        p = [x**power for x in p]
        p = [x / sum(p) for x in p]
    return p


def scores(
    rows: Rows,
    rho: float | dict[str, float] = P.DIXON_COLES_RHO,
    power: float = 1.0,
) -> dict[str, dict[int, float]]:
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for match_id, season, league, rh, ra, result in rows:
        r = rho.get(league, P.DIXON_COLES_RHO) if isinstance(rho, dict) else rho
        p = probabilities(rh, ra, r, power)
        out[season][match_id] = sum(
            (p[i] - (1.0 if i == result else 0.0)) ** 2 for i in range(3)
        )
    return out


def mean(values: dict[int, float]) -> float:
    return round(sum(values.values()) / len(values), 4)


def bootstrap(base: dict[int, float], other: dict[int, float]) -> dict[str, float]:
    diffs = [other[k] - base[k] for k in base if k in other]
    rng = random.Random(7)
    boots = sorted(
        sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(2000)
    )
    return {
        "diff": round(sum(diffs) / len(diffs), 4),
        "low": round(boots[50], 4),
        "high": round(boots[1949], 4),
        "p_better": sum(b < 0 for b in boots) / len(boots),
    }


def verdict(base: dict, variant: dict) -> dict[str, Any]:
    tune = mean(variant[TUNE]) - mean(base[TUNE])
    test = bootstrap(base[VALIDATE], variant[VALIDATE])
    ships = tune < 0 and test["diff"] < 0 and test["p_better"] >= SHIP_CONFIDENCE
    return {
        TUNE: mean(variant[TUNE]),
        VALIDATE: mean(variant[VALIDATE]),
        "bootstrap_25_26": test,
        "ships": ships,
    }


def save(name: str, result: dict[str, Any]) -> None:
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    results[name] = result
    CACHE.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(name, json.dumps(result, ensure_ascii=False), flush=True)


# --- experiments -------------------------------------------------------------


def run(names: list[str]) -> None:
    lab = Lab()
    base_rows = lab.rows("base", lambda m, d, league, f: P.team_ratings(m, d))
    base = scores(base_rows)
    save("base", {TUNE: mean(base[TUNE]), VALIDATE: mean(base[VALIDATE])})
    tune_rows = [r for r in base_rows if r[1] == TUNE]

    if "rho" in names:
        grid = (-0.2, -0.15, -0.1, -0.05, 0.0, 0.05)
        best = min(grid, key=lambda rho: mean(scores(tune_rows, rho)[TUNE]))
        save("rho", {"rho": best, **verdict(base, scores(base_rows, best))})

    if "calibration" in names:
        grid = (0.8, 0.9, 1.0, 1.1, 1.2, 1.3)
        best = min(grid, key=lambda p: mean(scores(tune_rows, power=p)[TUNE]))
        save(
            "calibration",
            {"power": best, **verdict(base, scores(base_rows, power=best))},
        )

    if "halflife" in names:
        tried = {}
        for days in (90, 180, 240):
            rows = lab.rows(
                f"halflife-{days}",
                lambda m, d, league, f, days=days: P.team_ratings(m, d, days),
            )
            tried[days] = scores(rows)
        best = min(tried, key=lambda days: mean(tried[days][TUNE]))
        save("halflife", {"days": best, **verdict(base, tried[best])})

    if "promoted" in names:
        tried = {}
        for attack in (0.8, 0.9):
            for defence in (1.1, 1.2):
                for weight in (2.0, 5.0):
                    name = f"promoted-{attack}-{defence}-{weight}"

                    def ratings(m, d, league, f, a=attack, df=defence, w=weight):
                        return P.team_ratings(
                            m,
                            d,
                            priors=dict.fromkeys(lab.promoted(league, f), (a, df)),
                            prior_matches=w,
                        )

                    tried[(attack, defence, weight)] = scores(lab.rows(name, ratings))
                    print(
                        name, mean(tried[(attack, defence, weight)][TUNE]), flush=True
                    )
        best = min(tried, key=lambda k: mean(tried[k][TUNE]))
        save("promoted", {"prior": list(best), **verdict(base, tried[best])})


def report() -> None:
    if not RESULTS.exists():
        sys.exit("No results yet: run `model_lab.py run all`.")
    print(RESULTS.read_text())


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "report"
    if command == "prepare":
        prepare()
    elif command == "run":
        wanted = sys.argv[2:] or ["all"]
        if "all" in wanted:
            wanted = ["rho", "calibration", "halflife", "promoted"]
        run(wanted)
    else:
        report()
