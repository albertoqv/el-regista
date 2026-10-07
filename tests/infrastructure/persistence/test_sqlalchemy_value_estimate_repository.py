import os
from datetime import date

import pytest

from player_scouting.domain.entities import Player
from player_scouting.domain.valuation import (
    ValuationReport,
    ValueEstimate,
    ValueFactor,
)
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_value_estimate_repository import (  # noqa: E501
    SqlAlchemyValueEstimateRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="DATABASE_URL is not set")

FACTORS = (ValueFactor("Liga", 1.8), ValueFactor("Edad", 0.7))


def _report(*estimates: ValueEstimate) -> ValuationReport:
    return ValuationReport(list(estimates), 4_000_000, 0.42, 9000)


def test_saves_each_estimate_with_its_factors_and_the_models_error(session):
    SqlAlchemyPlayerRepository(session).save_player(
        Player(1, "A", "Forward", date(2000, 1, 1))
    )
    repository = SqlAlchemyValueEstimateRepository(session)

    repository.save_value_estimates(
        _report(ValueEstimate(1, 25_000_000, FACTORS)), date(2026, 10, 7)
    )

    stored = repository.get_value_estimate(1)
    assert stored is not None
    assert (stored.estimate_eur, stored.factors) == (25_000_000, FACTORS)
    assert (stored.samples, stored.median_error) == (9000, 0.42)
    assert stored.computed_on == date(2026, 10, 7)
    assert repository.get_value_estimate(2) is None


def test_a_new_run_replaces_the_previous_one(session):
    players = SqlAlchemyPlayerRepository(session)
    for player_id in (1, 2):
        players.save_player(Player(player_id, "A", "Forward", date(2000, 1, 1)))
    repository = SqlAlchemyValueEstimateRepository(session)
    repository.save_value_estimates(
        _report(ValueEstimate(1, 1, FACTORS), ValueEstimate(2, 2, FACTORS)),
        date(2026, 10, 3),
    )

    repository.save_value_estimates(
        _report(ValueEstimate(2, 3, FACTORS)), date(2026, 10, 7)
    )

    assert [e.player_id for e in repository.list_value_estimates()] == [2]
    assert repository.get_value_estimate(2).estimate_eur == 3
