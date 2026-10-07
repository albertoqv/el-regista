from dataclasses import replace
from datetime import date

from player_scouting.application.use_cases.market_valuation import (
    EstimateMarketValuesUseCase,
)
from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from tests.application.doubles import (
    InMemoryCompetitionStatsRepository,
    InMemoryPlayerRepository,
    InMemoryValueEstimateRepository,
)

TODAY = date(2026, 10, 7)
LEAGUE = CompetitionLine(
    competition="La Liga",
    kind="league",
    season_label="2025",
    team="FC Barcelona",
    appearances=30,
    goals=10,
    assists=5,
    minutes_played=2700,
    yellow_cards=0,
    red_cards=0,
)


def _world():
    players = InMemoryPlayerRepository()
    competitions = InMemoryCompetitionStatsRepository(players)
    lines = {}
    for player_id in range(1, 61):
        players.save_player(
            Player(player_id, f"P{player_id}", "Forward", date(2000, 1, 1))
        )
        goals = player_id % 10
        lines[player_id] = [replace(LEAGUE, goals=goals)]
        players.save_market_value_history(
            player_id,
            [MarketValuePoint(date(2026, 6, 1), 5_000_000 + goals * 2_000_000, "X")],
        )
    # Valued, but without a finished season to judge him on: not estimated.
    players.save_player(Player(99, "Injured", "Forward", date(2000, 1, 1)))
    lines[99] = [replace(LEAGUE, season_label="2024")]
    competitions.save_competition_lines(lines)
    return players, competitions


def test_every_player_with_a_finished_season_gets_an_estimate():
    players, competitions = _world()
    estimates = InMemoryValueEstimateRepository()

    result = EstimateMarketValuesUseCase(
        players, competitions, estimates, today=lambda: TODAY
    ).execute()

    assert result.estimated == 60
    assert result.samples == 60
    assert estimates.get_value_estimate(99) is None
    stored = estimates.get_value_estimate(9)
    assert stored is not None
    assert stored.computed_on == TODAY
    # More goals, more value: the model follows the market it learnt from.
    assert stored.estimate_eur > estimates.get_value_estimate(1).estimate_eur
