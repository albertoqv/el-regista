from __future__ import annotations

from dataclasses import dataclass

SHOT_ON_TARGET_OUTCOMES = {"Goal", "Saved", "Saved to Post"}
TACKLE_WON_OUTCOMES = {"Won", "Success In Play", "Success Out", "Success"}
DISMISSAL_CARDS = {"Red Card", "Second Yellow"}

_SUMMABLE_FIELDS = (
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "expected_goals",
    "passes_completed",
    "passes_attempted",
    "key_passes",
    "dribbles_completed",
    "dribbles_attempted",
    "tackles_won",
    "interceptions",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "red_cards",
)


@dataclass
class PlayerMatchStats:
    player_id: int
    name: str
    position: str | None
    goals: int = 0
    assists: int = 0
    shots: int = 0
    shots_on_target: int = 0
    expected_goals: float = 0.0
    passes_completed: int = 0
    passes_attempted: int = 0
    key_passes: int = 0
    dribbles_completed: int = 0
    dribbles_attempted: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    fouls_committed: int = 0
    fouls_won: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


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
            shot = event.get("shot") or {}
            outcome_name = (shot.get("outcome") or {}).get("name")
            entry = entry_for(event)
            entry.shots += 1
            if outcome_name in SHOT_ON_TARGET_OUTCOMES:
                entry.shots_on_target += 1
            if outcome_name == "Goal":
                entry.goals += 1
            entry.expected_goals += shot.get("statsbomb_xg") or 0.0

        elif event_type == "Pass":
            pass_data = event.get("pass") or {}
            entry = entry_for(event)
            entry.passes_attempted += 1
            if "outcome" not in pass_data:
                entry.passes_completed += 1
            if pass_data.get("goal_assist") is True:
                entry.assists += 1
            if pass_data.get("shot_assist") is True:
                entry.key_passes += 1

        elif event_type == "Dribble":
            dribble = event.get("dribble") or {}
            entry = entry_for(event)
            entry.dribbles_attempted += 1
            if (dribble.get("outcome") or {}).get("name") == "Complete":
                entry.dribbles_completed += 1

        elif event_type == "Duel":
            duel = event.get("duel") or {}
            if (duel.get("type") or {}).get("name") == "Tackle":
                outcome_name = (duel.get("outcome") or {}).get("name")
                if outcome_name in TACKLE_WON_OUTCOMES:
                    entry_for(event).tackles_won += 1

        elif event_type == "Interception":
            entry_for(event).interceptions += 1

        elif event_type == "Foul Committed":
            entry = entry_for(event)
            entry.fouls_committed += 1
            card_name = (event.get("foul_committed") or {}).get("card", {}).get("name")
            if card_name == "Yellow Card":
                entry.yellow_cards += 1
            elif card_name in DISMISSAL_CARDS:
                entry.red_cards += 1

        elif event_type == "Foul Won":
            entry_for(event).fouls_won += 1

    return stats


def extract_lineup_players(lineups: list[dict]) -> dict[int, PlayerMatchStats]:
    players: dict[int, PlayerMatchStats] = {}
    for team_lineup in lineups:
        for player in team_lineup.get("lineup", []):
            positions = player.get("positions") or []
            position = positions[0].get("position") if positions else None
            players[player["player_id"]] = PlayerMatchStats(
                player["player_id"], player["player_name"], position
            )
    return players


def merge_statistics(
    accumulated: dict[int, PlayerMatchStats],
    match_stats: dict[int, PlayerMatchStats],
) -> dict[int, PlayerMatchStats]:
    for player_id, stats in match_stats.items():
        existing = accumulated.get(player_id)
        if existing is None:
            accumulated[player_id] = stats
        else:
            for field_name in _SUMMABLE_FIELDS:
                setattr(
                    existing,
                    field_name,
                    getattr(existing, field_name) + getattr(stats, field_name),
                )
    return accumulated
