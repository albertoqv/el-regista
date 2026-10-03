"""One name per club: FBref abbreviates ("Manchester Utd"), Understat does not.

Team pages and forecasts use Understat's names, so FBref's are translated with
what the players matched in both sources say: if most of a FBref team's players
play for one Understat team, that is the same club.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

MINIMUM_VOTES = 3
MINIMUM_SHARE = 0.6


def learn_team_aliases(
    pairs: Iterable[tuple[str | None, tuple[str, ...]]],
) -> dict[str, str]:
    """(FBref team, Understat teams) per matched player -> {FBref: Understat}."""
    votes: dict[str, Counter[str]] = defaultdict(Counter)
    for fbref_team, understat_teams in pairs:
        # Players who changed club tell nothing certain about either name.
        if not fbref_team or "," in fbref_team or len(understat_teams) != 1:
            continue
        votes[fbref_team][understat_teams[0]] += 1
    aliases = {}
    for fbref_team, counter in votes.items():
        understat_team, count = counter.most_common(1)[0]
        if (
            understat_team != fbref_team
            and count >= MINIMUM_VOTES
            and count / sum(counter.values()) >= MINIMUM_SHARE
        ):
            aliases[fbref_team] = understat_team
    return aliases


def renamed(team: str, old: str, new: str) -> str:
    """Renames one club inside a season's team text ("A" or "A, B")."""
    return ", ".join(new if part == old else part for part in team.split(", "))
