from datetime import date, datetime

import pytest

from player_scouting.application.ports import Fixture, TeamMatch
from player_scouting.application.use_cases.team_analytics import (
    BacktestUseCase,
    IngestTeamSeasonUseCase,
    LeagueTableUseCase,
    PredictFixturesUseCase,
)
from tests.application.doubles import InMemoryTeamRepository

NOW = datetime(2026, 10, 1, 12, 0)


def _side(match_id, day, team, opponent, home, gf, ga, xgf, xga, league="La Liga"):
    result = "w" if gf > ga else "d" if gf == ga else "l"
    return TeamMatch(
        match_id=match_id,
        competition=league,
        season_label="2026",
        played_on=date(2026, 9, day),
        team=team,
        opponent=opponent,
        home=home,
        goals_for=gf,
        goals_against=ga,
        xg_for=xgf,
        xg_against=xga,
        npxg_for=xgf,
        npxg_against=xga,
        ppda=8.0 if team == "Barcelona" else 14.0,
        ppda_allowed=14.0,
        deep=10,
        deep_allowed=4,
        xpts=2.2 if xgf > xga else 0.6,
        result=result,
    )


def _match(match_id, day, home, away, hg, ag, hxg, axg):
    fixture = Fixture(
        match_id,
        "La Liga",
        "2026",
        datetime(2026, 9, day, 20),
        home,
        away,
        hg,
        ag,
        hxg,
        axg,
    )
    sides = [
        _side(match_id, day, home, away, True, hg, ag, hxg, axg),
        _side(match_id, day, away, home, False, ag, hg, axg, hxg),
    ]
    return fixture, sides


def _repository():
    repository = InMemoryTeamRepository()
    played = [
        _match(1, 1, "Barcelona", "Getafe", 3, 0, 2.6, 0.5),
        _match(2, 8, "Getafe", "Sevilla", 1, 1, 0.9, 1.0),
        _match(3, 15, "Sevilla", "Barcelona", 0, 2, 0.6, 2.2),
        _match(4, 22, "Barcelona", "Sevilla", 1, 1, 2.0, 0.4),
        _match(5, 29, "Getafe", "Barcelona", 0, 1, 0.4, 1.9),
    ]
    upcoming = Fixture(
        6,
        "La Liga",
        "2026",
        datetime(2026, 10, 4, 21),
        "Barcelona",
        "Getafe",
        None,
        None,
        None,
        None,
    )
    far = Fixture(
        7,
        "La Liga",
        "2026",
        datetime(2026, 12, 4, 21),
        "Sevilla",
        "Getafe",
        None,
        None,
        None,
        None,
    )
    repository.save_team_season(
        [f for f, _ in played] + [upcoming, far],
        [side for _, sides in played for side in sides],
    )
    return repository


class FakeTeamProvider:
    def get_team_season(self, start_year):
        fixture, sides = _match(1, 1, "Barcelona", "Getafe", 3, 0, 2.6, 0.5)
        return [fixture], sides


def test_ingests_calendar_and_team_matches():
    repository = InMemoryTeamRepository()

    summary = IngestTeamSeasonUseCase(FakeTeamProvider(), repository).execute(2026)

    assert (summary.fixtures, summary.team_matches) == (1, 2)
    assert len(repository.list_team_matches(["2026"])) == 2


def test_league_table_with_expected_points_and_pressing():
    table = LeagueTableUseCase(_repository()).execute("2026", "La Liga")

    leader = table[0]
    assert leader.team == "Barcelona"
    assert (leader.played, leader.wins, leader.draws, leader.losses) == (4, 3, 1, 0)
    assert leader.points == 10
    assert (leader.goals_for, leader.goals_against) == (7, 1)
    assert leader.xpts == pytest.approx(8.8)
    assert leader.ppda == pytest.approx(8.0)
    # Latest first.
    assert leader.form == ["w", "d", "w", "w"]
    assert [row.team for row in table] == ["Barcelona", "Sevilla", "Getafe"]


def test_predicts_the_next_days_fixtures_only():
    forecasts = PredictFixturesUseCase(_repository(), now=lambda: NOW).execute(days=10)

    [forecast] = forecasts
    assert forecast.fixture.match_id == 6
    assert forecast.prediction.home_win > forecast.prediction.away_win
    assert forecast.home_form == ["w", "d", "w", "w"]


def test_backtest_scores_past_predictions_made_only_with_earlier_data():
    report = BacktestUseCase(_repository(), minimum_history=1).execute(["2026"])

    # Match 1 has no earlier data; later matches are forecast walk-forward.
    assert report.matches == 4
    assert 0 <= report.accuracy <= 1
    assert 0 <= report.brier <= 2
    assert report.baseline_brier > 0
    assert len(report.calibration) > 0
