import pytest

from player_scouting.domain.percentiles import per_90, percentile_profile
from player_scouting.domain.statistics import Statistics


def test_per_90_scales_a_metric_by_minutes_played():
    statistics = Statistics(goals=6, assists=0, minutes_played=540)

    assert per_90(statistics, "goals") == pytest.approx(1.0)


def test_per_90_is_zero_without_minutes():
    assert per_90(Statistics(goals=3, assists=0), "goals") == 0.0


def test_percentile_ranks_the_target_per_90_against_its_peers():
    target = Statistics(goals=9, assists=0, minutes_played=900)
    peers = [
        target,
        Statistics(goals=1, assists=0, minutes_played=900),
        Statistics(goals=3, assists=0, minutes_played=900),
        Statistics(goals=18, assists=0, minutes_played=900),
    ]

    profile = percentile_profile(target, peers)

    # Two peers below, itself counts half: (2 + 0.5) / 4.
    assert profile["goals"].percentile == 63
    assert profile["goals"].per_90 == pytest.approx(0.9)


def test_percentile_uses_rates_not_totals():
    target = Statistics(goals=5, assists=0, minutes_played=450)
    peers = [target, Statistics(goals=8, assists=0, minutes_played=1800)]

    profile = percentile_profile(target, peers)

    assert profile["goals"].percentile == 75


def test_metrics_nobody_has_recorded_are_left_out():
    target = Statistics(goals=2, assists=1, minutes_played=900)
    peers = [target, Statistics(goals=1, assists=0, minutes_played=900)]

    profile = percentile_profile(target, peers)

    assert "dribbles_completed" not in profile
    assert "goals" in profile
