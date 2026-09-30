from datetime import date

from player_scouting.application.use_cases.player_markets import (
    IngestRostersUseCase,
    PlayerMarketsBacktestUseCase,
    PlayerMarketsUseCase,
)

from player_scouting.application.ports import MatchRef, RosterEntry
from tests.application.doubles import InMemoryShotRepository
from tests.application.test_team_analytics import _repository as team_repository

LEAGUE = "La Liga"


def _line(
    match_id,
    day,
    team,
    opponent,
    player_id,
    name,
    position,
    minutes,
    goals=0,
    xg=0.1,
    yellow=0,
):
    return RosterEntry(
        match_id,
        LEAGUE,
        "2026",
        date(2026, 9, day),
        team,
        opponent,
        True,
        player_id,
        name,
        position,
        minutes,
        goals,
        0,
        0,
        2,
        1,
        xg,
        0.1,
        yellow,
        0,
    )


def _rosters():
    shots = InMemoryShotRepository()
    days = {
        1: ("Barcelona", "Getafe"),
        3: ("Sevilla", "Barcelona"),
        4: ("Barcelona", "Sevilla"),
        5: ("Getafe", "Barcelona"),
    }
    day_of = {1: 1, 3: 15, 4: 22, 5: 29}
    for match_id, (home, away) in days.items():
        day = day_of[match_id]
        opponent = away if home == "Barcelona" else home
        shots.save_rosters(
            match_id,
            [
                _line(
                    match_id,
                    day,
                    "Barcelona",
                    opponent,
                    1,
                    "Striker",
                    "FW",
                    90,
                    goals=1,
                    xg=0.7,
                ),
                _line(
                    match_id,
                    day,
                    "Barcelona",
                    opponent,
                    2,
                    "Hard Man",
                    "DMC",
                    90,
                    xg=0.02,
                    yellow=1,
                ),
                # The winger was dropped in the last two matches.
                _line(
                    match_id,
                    day,
                    "Barcelona",
                    opponent,
                    3,
                    "Winger",
                    "AML",
                    90 if match_id < 4 else 0,
                    xg=0.3,
                ),
                _line(
                    match_id, day, opponent, "Barcelona", 9, "Rival", "FW", 90, xg=0.3
                ),
            ],
        )
    return shots


def test_ingests_rosters_for_matches_that_do_not_have_them():
    class Provider:
        def get_match_rosters(self, match):
            return [
                _line(match.match_id, 1, "Barcelona", "Getafe", 1, "Striker", "FW", 90)
            ]

    shots = InMemoryShotRepository()
    shots.save_match(
        MatchRef(1, LEAGUE, "2026", date(2026, 9, 1), "Barcelona", "Getafe"), []
    )
    shots.save_match(
        MatchRef(2, LEAGUE, "2026", date(2026, 9, 8), "Getafe", "Sevilla"), []
    )

    summary = IngestRostersUseCase(Provider(), shots, pause=lambda s: None).execute(
        2026, limit=1
    )

    assert (summary.matches, summary.remaining) == (1, 1)


def test_player_markets_for_a_fixture():
    markets = PlayerMarketsUseCase(
        team_repository(), _rosters(), today=lambda: date(2026, 10, 1)
    ).execute(6)

    home = {line.name: line for line in markets.home}
    assert markets.fixture.home_team == "Barcelona"
    assert home["Striker"].props.goal > home["Hard Man"].props.goal
    assert home["Hard Man"].props.card > home["Striker"].props.card
    assert (
        home["Winger"].props.expected_minutes < home["Striker"].props.expected_minutes
    )
    assert [line.name for line in markets.away] == ["Rival"]


def test_backtest_of_the_anytime_scorer_market():
    report = PlayerMarketsBacktestUseCase(_rosters(), minimum_matches=1).execute(
        LEAGUE, "2026"
    )

    assert report.predictions > 0
    assert 0 <= report.brier <= 1 and 0 <= report.baseline_brier <= 1
