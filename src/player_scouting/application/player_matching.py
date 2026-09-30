from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Minutes played are counted slightly differently by each data source.
MINUTES_TOLERANCE = 15


@dataclass(frozen=True)
class MatchCandidate:
    player_id: int
    name: str
    team: str | None
    minutes: int
    goals: int


@dataclass(frozen=True)
class ExternalPlayer:
    external_id: int
    name: str
    teams: tuple[str, ...]
    minutes: int
    goals: int


def name_tokens(text: str) -> frozenset[str]:
    return _tokens(text)


def _tokens(text: str) -> frozenset[str]:
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    )
    return frozenset(re.sub(r"[^a-z ]", " ", ascii_text).split())


def _same_team(teams: tuple[str, ...], team: str | None) -> bool:
    if team is None:
        return False
    candidate_tokens = _tokens(team)
    return any(_tokens(external_team) & candidate_tokens for external_team in teams)


def _unique(candidates: list[MatchCandidate]) -> MatchCandidate | None:
    return candidates[0] if len(candidates) == 1 else None


def _find(
    external: ExternalPlayer, pool: list[MatchCandidate]
) -> MatchCandidate | None:
    name = _tokens(external.name)
    exact = _unique([c for c in pool if _tokens(c.name) == name])
    if exact is not None:
        return exact

    by_tokens = _unique(
        [c for c in pool if _tokens(c.name) <= name or name <= _tokens(c.name)]
    )
    if by_tokens is not None:
        return by_tokens

    return _unique(
        [
            c
            for c in pool
            if _same_team(external.teams, c.team)
            and abs(c.minutes - external.minutes) <= MINUTES_TOLERANCE
            and c.goals == external.goals
        ]
    )


def match_players(
    externals: list[ExternalPlayer], candidates: list[MatchCandidate]
) -> dict[int, int]:
    """Maps external ids to our player ids; unmatched externals are left out."""
    available = list(candidates)
    matches: dict[int, int] = {}
    for external in externals:
        match = _find(external, available)
        if match is not None:
            matches[external.external_id] = match.player_id
            available.remove(match)
    return matches
