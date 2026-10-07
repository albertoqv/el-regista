from datetime import date

from fastapi.testclient import TestClient

from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.valuation import ValuationReport, ValueEstimate, ValueFactor
from player_scouting.presentation.api.dependencies import (
    get_competition_stats_repository,
    get_player_repository,
    get_value_estimate_repository,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    InMemoryCompetitionStatsRepository,
    InMemoryPlayerRepository,
    InMemoryValueEstimateRepository,
)

FACTORS = (ValueFactor("Liga", 1.8), ValueFactor("Edad", 0.7))


def _client() -> tuple[TestClient, InMemoryValueEstimateRepository]:
    players = InMemoryPlayerRepository()
    for player_id, name, value in (
        (1, "Cheap", 5_000_000),
        (2, "Pricey", 80_000_000),
        (3, "Fair", 20_000_000),
        (4, "Tiny", 300_000),
    ):
        players.save_player(Player(player_id, name, "Forward", date(2000, 1, 1)))
        players.save_market_value_history(
            player_id, [MarketValuePoint(date(2026, 6, 1), value, "X")]
        )
    estimates = InMemoryValueEstimateRepository()
    estimates.save_value_estimates(
        ValuationReport(
            [
                ValueEstimate(1, 15_000_000, FACTORS),
                ValueEstimate(2, 40_000_000, FACTORS),
                ValueEstimate(3, 22_000_000, FACTORS),
                ValueEstimate(4, 9_000_000, FACTORS),
            ],
            4_000_000,
            0.38,
            9000,
        ),
        date(2026, 10, 7),
    )
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: players
    app.dependency_overrides[get_value_estimate_repository] = lambda: estimates
    app.dependency_overrides[get_competition_stats_repository] = lambda: (
        InMemoryCompetitionStatsRepository(players)
    )
    return TestClient(app), estimates


def test_a_players_estimate_next_to_his_market_value_and_why():
    client, _ = _client()

    body = client.get("/players/1/value-estimate").json()

    assert body["estimate_eur"] == 15_000_000
    assert body["market_eur"] == 5_000_000
    assert body["factors"] == [
        {"label": "Liga", "factor": 1.8},
        {"label": "Edad", "factor": 0.7},
    ]
    assert body["model"] == {"samples": 9000, "median_error": 0.38}
    assert body["computed_on"] == "2026-10-07"


def test_a_player_without_an_estimate_is_404():
    client, _ = _client()

    assert client.get("/players/99/value-estimate").status_code == 404


def test_the_most_undervalued_players_first_with_a_real_price_tag():
    client, _ = _client()

    body = client.get("/players/value-gaps?limit=5").json()

    # Tiny is "cheap" too, but a 300k valuation is noise, not a bargain.
    assert [row["name"] for row in body] == ["Cheap", "Fair"]
    assert body[0]["ratio"] == 3.0


def test_keepers_and_veterans_stay_off_the_bargains_list():
    # The model has no keeper numbers, and the market rightly discounts a 33-year-old.
    client, estimates = _client()
    players = client.app.dependency_overrides[get_player_repository]()
    players.save_player(Player(5, "Keeper", "Goalkeeper", date(2000, 1, 1)))
    players.save_player(Player(6, "Veteran", "Forward", date(1993, 1, 1)))
    for player_id in (5, 6):
        players.save_market_value_history(
            player_id, [MarketValuePoint(date(2026, 6, 1), 2_000_000, "X")]
        )
    report = ValuationReport(
        [ValueEstimate(p, 20_000_000, FACTORS) for p in (1, 3, 5, 6)],
        4_000_000,
        0.4,
        9000,
    )
    estimates.save_value_estimates(report, date(2026, 10, 7))

    body = client.get("/players/value-gaps?limit=5").json()

    assert [row["name"] for row in body] == ["Cheap"]
