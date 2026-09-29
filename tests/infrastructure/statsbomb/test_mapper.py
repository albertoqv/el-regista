from player_scouting.infrastructure.statsbomb.mapper import (
    PlayerMatchStats,
    extract_player_statistics,
    merge_statistics,
)

SCORER = {"id": 101, "name": "Scorer Player"}
ASSISTER = {"id": 102, "name": "Assister Player"}


def _shot_event(player: dict, outcome_name: str) -> dict:
    return {
        "type": {"id": 16, "name": "Shot"},
        "player": player,
        "position": {"id": 23, "name": "Center Forward"},
        "shot": {"outcome": {"id": 97, "name": outcome_name}},
    }


def _pass_event(player: dict, goal_assist: bool) -> dict:
    return {
        "type": {"id": 30, "name": "Pass"},
        "player": player,
        "position": {"id": 15, "name": "Left Wing"},
        "pass": {"goal_assist": goal_assist},
    }


def test_counts_a_goal_from_a_shot_event():
    events = [_shot_event(SCORER, "Goal")]

    stats = extract_player_statistics(events)

    assert stats[101].goals == 1
    assert stats[101].assists == 0
    assert stats[101].name == "Scorer Player"
    assert stats[101].position == "Center Forward"


def test_does_not_count_a_shot_that_is_not_a_goal():
    events = [_shot_event(SCORER, "Off T")]

    stats = extract_player_statistics(events)

    assert stats == {}


def test_counts_an_assist_from_a_pass_event():
    events = [_pass_event(ASSISTER, goal_assist=True)]

    stats = extract_player_statistics(events)

    assert stats[102].assists == 1
    assert stats[102].goals == 0


def test_does_not_count_a_pass_without_goal_assist():
    events = [_pass_event(ASSISTER, goal_assist=False)]

    stats = extract_player_statistics(events)

    assert stats == {}


def test_ignores_own_goal_events():
    own_goal_event = {
        "type": {"id": 25, "name": "Own Goal Against"},
        "player": SCORER,
    }

    stats = extract_player_statistics([own_goal_event])

    assert stats == {}


def test_accumulates_goals_and_assists_for_the_same_player_across_events():
    events = [
        _shot_event(SCORER, "Goal"),
        _shot_event(SCORER, "Goal"),
        _pass_event(SCORER, goal_assist=True),
    ]

    stats = extract_player_statistics(events)

    assert stats[101].goals == 2
    assert stats[101].assists == 1


def test_merge_statistics_adds_goals_and_assists_for_a_player_present_in_both_matches():
    accumulated = {
        101: PlayerMatchStats(101, "Scorer Player", "Center Forward", goals=1)
    }
    match_stats = {
        101: PlayerMatchStats(101, "Scorer Player", "Center Forward", goals=2)
    }

    merged = merge_statistics(accumulated, match_stats)

    assert merged[101].goals == 3


def test_merge_statistics_keeps_a_player_only_present_in_the_new_match():
    accumulated: dict[int, PlayerMatchStats] = {}
    match_stats = {
        102: PlayerMatchStats(102, "Assister Player", "Left Wing", assists=1)
    }

    merged = merge_statistics(accumulated, match_stats)

    assert merged[102].assists == 1
