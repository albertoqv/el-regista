import pytest

from player_scouting.domain.shots import (
    LATE_MINUTE,
    Shot,
    distance_to_goal,
    is_outside_box,
    mark_decisive_goals,
)


def _shot(minute: int, home: bool, result: str = "Goal", **overrides) -> Shot:
    values = {
        "shot_id": minute * 10 + (1 if home else 2),
        "match_id": 1,
        "understat_player_id": 7,
        "player_name": "Someone",
        "minute": minute,
        "result": result,
        "x": 0.9,
        "y": 0.5,
        "xg": 0.3,
        "situation": "OpenPlay",
        "shot_type": "RightFoot",
        "home": home,
        "assisted_by": None,
    }
    values.update(overrides)
    return Shot(**values)


def test_distance_is_measured_in_metres_on_a_105_by_68_pitch():
    # Penalty spot: 11 m out, centred.
    assert distance_to_goal(1 - 11 / 105, 0.5) == pytest.approx(11.0)


def test_shots_beyond_the_18_yard_line_are_outside_the_box():
    assert is_outside_box(0.80, 0.5)
    assert not is_outside_box(0.90, 0.5)
    # Level with the box line but out wide is outside too.
    assert is_outside_box(0.90, 0.05)


def test_late_goals_start_at_minute_75():
    assert LATE_MINUTE == 75


def test_goals_that_equalise_or_take_the_lead_are_decisive():
    shots = [
        _shot(10, home=True),  # 1-0 lead: decisive
        _shot(20, home=True),  # 2-0: not decisive
        _shot(30, home=False),  # 2-1: not decisive
        _shot(40, home=False),  # 2-2 equaliser: decisive
        _shot(50, home=False, result="SavedShot"),
        _shot(90, home=False),  # 2-3 winner: decisive
    ]

    marked = mark_decisive_goals(shots)

    assert [s.minute for s in marked if s.decisive] == [10, 40, 90]


def test_own_goals_count_for_the_score_but_are_never_decisive_for_the_shooter():
    shots = [
        # Verified live (Levante 2-3 Barcelona): an own goal is listed on the side
        # of the player who scores it and counts for the opponent.
        _shot(10, home=True, result="OwnGoal"),  # 0-1
        _shot(60, home=True),  # 1-1 equaliser: decisive
    ]

    marked = mark_decisive_goals(shots)

    assert [s.decisive for s in marked] == [False, True]
