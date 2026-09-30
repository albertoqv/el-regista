import math

import pytest

from player_scouting.domain.player_props import (
    Appearance,
    expected_minutes,
    player_props,
    position_group,
)


def _apps(count, minutes=90, xg=0.5, xa=0.2, shots=3, yellow=0, position="FW"):
    return [Appearance(minutes, xg, xa, shots, yellow, position) for _ in range(count)]


def test_positions_are_grouped():
    assert position_group("FW") == "forward"
    assert position_group("AML") == "attacking"
    assert position_group("DMC") == "midfield"
    assert position_group("DR") == "defence"
    assert position_group("GK") == "goalkeeper"


def test_expected_minutes_weigh_the_latest_matches_more():
    # Played the last 3, missed the 3 before (latest first).
    back_in_team = expected_minutes([90, 90, 90, 0, 0, 0])
    dropped = expected_minutes([0, 0, 0, 90, 90, 90])

    assert back_in_team > 45 > dropped


def test_a_regular_striker_is_likely_to_score_and_scales_with_the_match():
    history = _apps(20, xg=0.6)

    normal = player_props(history, minutes=90, team_factor=1.0, card_factor=1.0)
    easier = player_props(history, minutes=90, team_factor=1.5, card_factor=1.0)

    assert normal.goal == pytest.approx(1 - math.exp(-normal.expected_goals))
    assert 0.35 < normal.goal < 0.55
    assert easier.goal > normal.goal
    assert normal.shots_1 > normal.shots_2 > 0


def test_few_minutes_lean_on_the_position_average():
    lucky_cameo = [Appearance(20, 1.5, 0.0, 2, 0, "DC")]

    props = player_props(lucky_cameo, minutes=90, team_factor=1.0, card_factor=1.0)

    # One lucky shot must not turn a centre-back into a top scorer.
    assert props.goal < 0.25


def test_playing_less_lowers_every_probability():
    history = _apps(20, yellow=0)
    history[0] = Appearance(90, 0.5, 0.2, 3, 1, "FW")

    starter = player_props(history, minutes=90, team_factor=1.0, card_factor=1.0)
    sub = player_props(history, minutes=25, team_factor=1.0, card_factor=1.0)

    assert sub.goal < starter.goal
    assert sub.assist < starter.assist
    assert sub.card < starter.card


def test_playing_chance_and_minutes_when_he_plays_are_separate():
    from player_scouting.domain.player_props import minutes_when_playing, playing_chance

    rotated = [90, 0, 90, 0, 90, 0]  # latest first

    assert minutes_when_playing(rotated) == pytest.approx(90)
    assert 0.5 < playing_chance(rotated) < 0.7
    assert playing_chance([0, 0, 0]) == 0
    assert minutes_when_playing([0, 0]) == 0
