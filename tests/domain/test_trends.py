from datetime import date

from player_scouting.domain.trends import MatchLine, build_trend


def _line(day, xg, xa=0.0, minutes=90, goals=0):
    return MatchLine(
        played_on=date(2026, 8, day),
        opponent="Rival",
        home=True,
        minutes=minutes,
        goals=goals,
        assists=0,
        shots=2,
        xg=xg,
        xa=xa,
    )


def test_each_match_carries_the_rolling_threat_per_90():
    trend = build_trend([_line(1, 0.2), _line(8, 0.4), _line(15, 0.6)], window=2)

    assert [round(p.rolling_per90, 2) for p in trend.points] == [0.2, 0.3, 0.5]


def test_a_player_creating_more_lately_is_on_the_rise():
    lines = [_line(day, 0.1) for day in range(1, 11)] + [
        _line(day, 0.6) for day in range(11, 16)
    ]

    assert build_trend(lines, window=5).direction == "up"


def test_steady_numbers_are_steady_and_cold_streaks_go_down():
    steady = [_line(day, 0.3) for day in range(1, 16)]
    cooling = [_line(day, 0.6) for day in range(1, 11)] + [
        _line(day, 0.1) for day in range(11, 16)
    ]

    assert build_trend(steady, window=5).direction == "steady"
    assert build_trend(cooling, window=5).direction == "down"


def test_finishing_compares_goals_with_expected_goals():
    trend = build_trend([_line(1, 0.5, goals=2), _line(8, 0.5, goals=1)], window=5)

    assert round(trend.goals_minus_xg, 2) == 2.0


def test_matches_off_the_bench_count_by_minutes_and_unused_ones_are_dropped():
    trend = build_trend([_line(1, 0.9, minutes=45), _line(8, 0.0, minutes=0)], window=5)

    assert len(trend.points) == 1
    assert round(trend.points[0].rolling_per90, 2) == 1.8


def test_too_few_matches_give_no_direction():
    assert build_trend([_line(1, 0.3)], window=5).direction is None
