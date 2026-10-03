"""How far apart two detailed roles are (Transfermarkt's names).

Roles are nodes of a small graph whose edges join the ones a player moves
between: mirrored sides, neighbouring lines. The distance is the number of steps.
"""

from __future__ import annotations

from collections import deque
from typing import Literal

_NEIGHBOURS = (
    ("Centre-Back", "Defensive Midfield"),
    ("Centre-Back", "Left-Back"),
    ("Centre-Back", "Right-Back"),
    ("Left-Back", "Right-Back"),
    ("Left-Back", "Left Midfield"),
    ("Right-Back", "Right Midfield"),
    ("Defensive Midfield", "Central Midfield"),
    ("Central Midfield", "Attacking Midfield"),
    ("Central Midfield", "Left Midfield"),
    ("Central Midfield", "Right Midfield"),
    ("Left Midfield", "Right Midfield"),
    ("Left Midfield", "Left Winger"),
    ("Right Midfield", "Right Winger"),
    ("Left Winger", "Right Winger"),
    ("Attacking Midfield", "Second Striker"),
    ("Left Winger", "Second Striker"),
    ("Right Winger", "Second Striker"),
    ("Second Striker", "Centre-Forward"),
)
_GRAPH: dict[str, set[str]] = {}
for _a, _b in _NEIGHBOURS:
    _GRAPH.setdefault(_a, set()).add(_b)
    _GRAPH.setdefault(_b, set()).add(_a)
_GRAPH["Goalkeeper"] = set()

# Roles this close count as one position for twins (a winger and a wide midfielder).
HYBRID_DISTANCE = 1
# Similarity points lost per distance: a neighbour costs little, far roles a lot.
_PENALTIES = {0: 0, 1: 4, 2: 10}
FAR_PENALTY = 20

RoleMatch = Literal["same", "similar", "different"]


def role_distance(first: str | None, second: str | None) -> int | None:
    if first not in _GRAPH or second not in _GRAPH:
        return None
    seen = {first: 0}
    queue = deque([first])
    while queue:
        role = queue.popleft()
        if role == second:
            return seen[role]
        for neighbour in _GRAPH[role]:
            if neighbour not in seen:
                seen[neighbour] = seen[role] + 1
                queue.append(neighbour)
    return 99


def role_penalty(distance: int | None) -> int:
    if distance is None:
        return 0
    return _PENALTIES.get(distance, FAR_PENALTY)


def role_match(distance: int | None) -> RoleMatch | None:
    if distance is None:
        return None
    if distance == 0:
        return "same"
    return "similar" if distance == 1 else "different"
