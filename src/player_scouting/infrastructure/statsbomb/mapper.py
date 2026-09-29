from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlayerMatchStats:
    player_id: int
    name: str
    position: str | None
    goals: int = 0
    assists: int = 0


def extract_player_statistics(events: list[dict]) -> dict[int, PlayerMatchStats]:
    stats: dict[int, PlayerMatchStats] = {}

    def entry_for(event: dict) -> PlayerMatchStats:
        player = event["player"]
        player_id = player["id"]
        if player_id not in stats:
            position = (event.get("position") or {}).get("name")
            stats[player_id] = PlayerMatchStats(player_id, player["name"], position)
        return stats[player_id]

    for event in events:
        event_type = event.get("type", {}).get("name")
        if event_type == "Shot":
            outcome = (event.get("shot") or {}).get("outcome") or {}
            if outcome.get("name") == "Goal":
                entry_for(event).goals += 1
        elif event_type == "Pass":
            if (event.get("pass") or {}).get("goal_assist") is True:
                entry_for(event).assists += 1

    return stats


