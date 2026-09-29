from datetime import date

import pytest

from player_scouting.domain.market_value import MarketValuePoint


def test_market_value_point_guarda_sus_datos():
    punto = MarketValuePoint(
        as_of=date(2019, 10, 17), amount_eur=2_500_000, club="Birmingham City"
    )

    assert punto.as_of == date(2019, 10, 17)
    assert punto.amount_eur == 2_500_000
    assert punto.club == "Birmingham City"


def test_market_value_point_es_inmutable():
    punto = MarketValuePoint(
        as_of=date(2019, 10, 17), amount_eur=2_500_000, club="Birmingham City"
    )

    with pytest.raises(AttributeError):
        punto.amount_eur = 1
