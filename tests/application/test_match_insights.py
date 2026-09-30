from datetime import date, datetime

import pytest

from player_scouting.application.ports import Fixture, MatchStats
from player_scouting.application.use_cases.match_insights import (
    IngestMatchStatsUseCase,
    MatchInsightsUseCase,
    StatsBacktestUseCase,
    learn_team_names,
)
from tests.application.doubles import (
    InMemoryMatchStatsRepository,
)
from tests.application.test_team_analytics import _repository as team_repository

LEAGUE = "La Liga"


def _stats(
    day, home, away, hg, ag, corners=(6, 4), yellows=(2, 2), referee="Ref Normal"
):
    return MatchStats(
        LEAGUE,
        "2026",
        date(2026, 9, day),
        home,
        away,
        referee,
        home_goals=hg,
        away_goals=ag,
        home_goals_ht=hg // 2,
        away_goals_ht=ag // 2,
        home_shots=15,
        away_shots=9,
        home_shots_on_target=6,
        away_shots_on_target=3,
        home_fouls=11,
        away_fouls=13,
        home_corners=corners[0],
        away_corners=corners[1],
        home_yellows=yellows[0],
        away_yellows=yellows[1],
        home_reds=0,
        away_reds=0,
        odds_home=1.8,
        odds_draw=3.6,
        odds_away=4.5,
    )


def _stats_repository():
    repository = InMemoryMatchStatsRepository()
    # Same dates and scores as the Understat fixtures in team_repository(),
    # with football-data's spelling of the names.
    repository.save_match_stats(
        [
            _stats(1, "Barcelona", "Getafe", 3, 0, corners=(9, 2)),
            _stats(8, "Getafe", "Sevilla", 1, 1, yellows=(4, 4), referee="Ref Strict"),
            _stats(15, "Sevilla", "Barcelona", 0, 2, corners=(3, 8)),
            _stats(
                22,
                "Barcelona",
                "Sevilla",
                1,
                1,
                corners=(10, 3),
                yellows=(5, 3),
                referee="Ref Strict",
            ),
            _stats(29, "Getafe", "Barcelona", 0, 1, corners=(2, 7)),
            MatchStats(
                LEAGUE,
                "2026",
                date(2026, 10, 4),
                "Barcelona",
                "Getafe",
                "Ref Strict",
                odds_home=1.3,
                odds_draw=5.5,
                odds_away=10.0,
            ),
        ]
    )
    return repository


def test_learns_that_two_sources_name_teams_differently():
    fixtures = [
        Fixture(
            1,
            LEAGUE,
            "2026",
            datetime(2026, 9, 1, 21),
            "Rayo Vallecano",
            "Athletic Club",
            2,
            1,
            1.5,
            1.0,
        ),
        Fixture(
            2,
            LEAGUE,
            "2026",
            datetime(2026, 9, 8, 21),
            "Athletic Club",
            "Getafe",
            0,
            0,
            0.8,
            0.7,
        ),
    ]
    stats = [
        _stats(1, "Vallecano", "Ath Bilbao", 2, 1),
        _stats(8, "Ath Bilbao", "Getafe", 0, 0),
    ]

    names = learn_team_names(fixtures, stats)

    assert names == {
        "Rayo Vallecano": "Vallecano",
        "Athletic Club": "Ath Bilbao",
        "Getafe": "Getafe",
    }


def test_ingests_seasons_and_upcoming_odds():
    class Provider:
        def season(self, start_year):
            return [_stats(1, "Barcelona", "Getafe", 3, 0)]

        def upcoming(self):
            return [
                MatchStats(
                    LEAGUE,
                    "2026",
                    date(2026, 10, 4),
                    "Barcelona",
                    "Getafe",
                    "Ref Strict",
                )
            ]

    repository = InMemoryMatchStatsRepository()

    saved = IngestMatchStatsUseCase(Provider(), repository).execute(2026)

    assert saved == 2
    assert len(repository.list_match_stats(LEAGUE, ["2026"])) == 2


def test_match_insights_cover_result_goals_and_every_stat():
    insights = MatchInsightsUseCase(
        team_repository(), _stats_repository(), today=lambda: date(2026, 10, 1)
    ).execute(6)

    assert insights.fixture.home_team == "Barcelona"
    assert insights.result.home_win > insights.result.away_win
    home, draw, away = insights.market
    assert home > 0.7 and home + draw + away == pytest.approx(1.0)
    assert insights.consensus[0] == pytest.approx((insights.result.home_win + home) / 2)
    assert set(insights.goals_over) == {0.5, 1.5, 2.5, 3.5, 4.5}
    assert insights.goals_over[0.5] > insights.goals_over[2.5]
    assert sum(insights.half_time) == pytest.approx(1.0)
    assert set(insights.stats) == {
        "corners",
        "yellows",
        "fouls",
        "shots",
        "shots_on_target",
    }
    corners = insights.stats["corners"]
    assert corners.expected_home > corners.expected_away  # Barcelona wins corners
    # The referee of this match shows more cards than the league average.
    assert insights.referee is not None and insights.referee.name == "Ref Strict"
    assert insights.referee.multiplier > 1
    assert [m.played_on for m in insights.head_to_head] == [
        date(2026, 9, 1),
        date(2026, 9, 29),
    ][::-1]
    assert len(insights.home_recent) == 4


def test_stats_backtest_compares_against_the_league_average():
    report = StatsBacktestUseCase(_stats_repository(), minimum_history=2).execute(
        LEAGUE, "2026"
    )

    corners = report["corners"]
    assert corners.matches == 3
    assert corners.model_mae >= 0 and corners.baseline_mae >= 0
