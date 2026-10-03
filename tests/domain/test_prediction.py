from datetime import date

import pytest

from player_scouting.domain.prediction import (
    TeamMatchRecord,
    predict,
    score_matrix,
    team_ratings,
)

TODAY = date(2026, 10, 1)


def _match(team, opponent, home, day, gf, ga, xgf, xga):
    return TeamMatchRecord(
        team=team,
        opponent=opponent,
        home=home,
        played_on=date(2026, 9, day),
        goals_for=gf,
        goals_against=ga,
        xg_for=xgf,
        xg_against=xga,
    )


def _both_sides(home, away, day, hg, ag, hxg, axg):
    return [
        _match(home, away, True, day, hg, ag, hxg, axg),
        _match(away, home, False, day, ag, hg, axg, hxg),
    ]


def test_score_matrix_is_a_probability_distribution():
    matrix = score_matrix(1.4, 1.1)

    assert sum(sum(row) for row in matrix) == pytest.approx(1.0, abs=1e-6)


def test_dixon_coles_makes_low_score_draws_more_likely_than_plain_poisson():
    plain = score_matrix(1.2, 1.2, rho=0.0)
    corrected = score_matrix(1.2, 1.2, rho=-0.1)

    assert corrected[0][0] > plain[0][0]
    assert corrected[1][1] > plain[1][1]


def test_prediction_probabilities_add_up_and_favour_the_stronger_side():
    matches = (
        _both_sides("Strong", "Weak", 1, 3, 0, 2.8, 0.4)
        + _both_sides("Weak", "Mid", 8, 1, 1, 1.0, 1.1)
        + _both_sides("Mid", "Strong", 15, 0, 2, 0.7, 2.1)
    )
    ratings = team_ratings(matches, TODAY)

    prediction = predict(ratings, "Strong", "Weak")

    total = prediction.home_win + prediction.draw + prediction.away_win
    assert total == pytest.approx(1.0, abs=1e-6)
    assert prediction.home_win > 0.5
    assert prediction.expected_home > prediction.expected_away
    assert len(prediction.scorelines) == 5
    assert 0 < prediction.over_2_5 < 1
    assert 0 < prediction.both_teams_score < 1


def test_ratings_shrink_small_samples_towards_the_average():
    one_game = _both_sides("Lucky", "Unlucky", 20, 5, 0, 4.0, 0.2)

    ratings = team_ratings(one_game, TODAY)

    # One huge game must not make a team five times better than average.
    assert 1.0 < ratings.attack["Lucky"] < 2.0
    assert 0.5 < ratings.attack["Unlucky"] < 1.0


def test_recent_matches_weigh_more_than_old_ones():
    old_good = [
        _match("A", "X", True, 1, 3, 0, 3.0, 0.3),
        _match("X", "A", False, 1, 0, 3, 0.3, 3.0),
    ]
    recent_bad = [
        _match("A", "Y", True, 28, 0, 2, 0.4, 2.0),
        _match("Y", "A", False, 28, 2, 0, 2.0, 0.4),
    ]
    plus_filler = _both_sides("X", "Y", 15, 1, 1, 1.2, 1.2)

    ratings = team_ratings(old_good + recent_bad + plus_filler, TODAY, half_life_days=7)

    assert ratings.attack["A"] < 1.0


def test_unknown_teams_are_rated_as_average():
    ratings = team_ratings(_both_sides("A", "B", 1, 1, 1, 1.0, 1.0), TODAY)

    prediction = predict(ratings, "Promoted", "A")

    assert prediction.home_win > prediction.away_win  # only home advantage splits them


def test_a_team_can_shrink_towards_its_own_prior_instead_of_the_average():
    games = _both_sides("Promoted", "Rival", 20, 1, 1, 1.2, 1.2)

    neutral = team_ratings(games, TODAY)
    weaker = team_ratings(
        games, TODAY, priors={"Promoted": (0.8, 1.2)}, prior_matches=5.0
    )

    assert weaker.attack["Promoted"] < neutral.attack["Promoted"]
    assert weaker.defence["Promoted"] > neutral.defence["Promoted"]
    # Teams without a prior keep the usual shrinkage towards the average.
    assert weaker.attack["Rival"] == pytest.approx(neutral.attack["Rival"], rel=0.1)
