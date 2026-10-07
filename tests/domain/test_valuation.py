import math

from player_scouting.domain.valuation import (
    ValuationInput,
    estimate_values,
)


def _player(player_id: int, **values) -> ValuationInput:
    base = dict(
        player_id=player_id,
        age=24.0,
        position="Forward",
        league="La Liga",
        minutes=2000,
        goals_per90=0.3,
        assists_per90=0.1,
        europe_appearances=0,
        national_appearances=0,
        market_value_eur=None,
    )
    base.update(values)
    return ValuationInput(**base)


def _world() -> list[ValuationInput]:
    """A market where a La Liga player is worth twice an Eredivisie one and each
    0.1 goals per 90 adds 20%: the model must find both."""
    players = []
    for index in range(400):
        league = "La Liga" if index % 2 else "Eredivisie"
        goals = (index % 7) / 10
        value = 10_000_000 * (2 if league == "La Liga" else 1) * math.exp(goals * 1.823)
        players.append(
            _player(
                index, league=league, goals_per90=goals, market_value_eur=int(value)
            )
        )
    return players


def test_the_model_learns_what_the_market_pays_for():
    report = estimate_values(_world())

    by_id = {estimate.player_id: estimate for estimate in report.estimates}
    # Player 1: La Liga, 0.1 goals per 90 -> 20M * e^0.1823 ~ 24M.
    assert abs(by_id[1].estimate_eur / 24_000_000 - 1) < 0.05
    assert report.median_error < 0.05
    assert report.samples == 400


def test_each_estimate_explains_itself_with_factors_that_multiply_up():
    report = estimate_values(_world())

    estimate = next(e for e in report.estimates if e.player_id == 1)
    product = report.average_eur
    for factor in estimate.factors:
        product *= factor.factor
    assert abs(product / estimate.estimate_eur - 1) < 0.01
    assert {factor.label for factor in estimate.factors} >= {"Liga", "Goles"}


def test_players_without_a_market_value_are_estimated_but_not_learnt_from():
    world = _world() + [_player(999, league="La Liga", goals_per90=0.0)]

    report = estimate_values(world)

    newcomer = next(e for e in report.estimates if e.player_id == 999)
    assert abs(newcomer.estimate_eur / 20_000_000 - 1) < 0.05
    assert report.samples == 400
