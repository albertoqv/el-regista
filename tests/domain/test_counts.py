from datetime import date

import pytest

from player_scouting.domain.counts import (
    CountRecord,
    count_ratings,
    dispersion,
    negative_binomial_pmf,
    stat_prediction,
)
from player_scouting.domain.market import implied_probabilities

TODAY = date(2026, 10, 1)


def _both(home, away, day, home_value, away_value):
    return [
        CountRecord(home, away, True, date(2026, 9, day), home_value, away_value),
        CountRecord(away, home, False, date(2026, 9, day), away_value, home_value),
    ]


def test_negative_binomial_is_a_distribution_wider_than_poisson():
    narrow = [negative_binomial_pmf(k, 5.0, dispersion=1000.0) for k in range(60)]
    wide = [negative_binomial_pmf(k, 5.0, dispersion=3.0) for k in range(60)]

    assert sum(narrow) == pytest.approx(1.0, abs=1e-6)
    assert sum(wide) == pytest.approx(1.0, abs=1e-6)
    assert wide[0] > narrow[0]  # fatter tails


def test_dispersion_is_estimated_from_mean_and_variance():
    # Var = mean + mean^2 / k  ->  k = mean^2 / (var - mean)
    assert dispersion([2, 4, 6, 8]) == pytest.approx(5**2 / (20 / 3 - 5))
    assert dispersion([5, 5, 5, 5]) >= 100  # no overdispersion: close to Poisson


def test_counts_follow_each_teams_tendency_and_the_opponent():
    records = (
        _both("Attackers", "Parkers", 1, 9, 2)
        + _both("Parkers", "Middle", 8, 3, 5)
        + _both("Middle", "Attackers", 15, 4, 7)
    )
    ratings = count_ratings(records, TODAY)

    prediction = stat_prediction(
        ratings, "Attackers", "Parkers", dispersion=6.0, lines=(8.5, 10.5)
    )

    assert prediction.expected_home > prediction.expected_away
    assert (
        prediction.home_more + prediction.equal + prediction.away_more
        == pytest.approx(1.0, abs=1e-6)
    )
    assert prediction.home_more > prediction.away_more
    assert prediction.over[8.5] > prediction.over[10.5]
    assert prediction.expected_total == pytest.approx(
        prediction.expected_home + prediction.expected_away
    )


def test_a_multiplier_scales_both_sides_like_a_strict_referee():
    ratings = count_ratings(_both("A", "B", 1, 2, 2), TODAY)

    normal = stat_prediction(ratings, "A", "B", dispersion=6.0, lines=(3.5,))
    strict = stat_prediction(
        ratings, "A", "B", dispersion=6.0, lines=(3.5,), multiplier=1.3
    )

    assert strict.expected_total == pytest.approx(normal.expected_total * 1.3)
    assert strict.over[3.5] > normal.over[3.5]


def test_implied_probabilities_remove_the_bookmaker_margin():
    home, draw, away = implied_probabilities(2.0, 3.5, 4.0)

    assert home + draw + away == pytest.approx(1.0)
    assert home > draw > away
    assert home == pytest.approx((1 / 2.0) / (1 / 2.0 + 1 / 3.5 + 1 / 4.0))
