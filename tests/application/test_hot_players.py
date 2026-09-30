from dataclasses import replace
from datetime import date

import pytest

from player_scouting.application.use_cases.hot_players import HotPlayersUseCase
from tests.application.doubles import InMemoryShotRepository
from tests.application.test_player_markets import _line


def _repository():
    shots = InMemoryShotRepository()
    lines = []
    # Striker: quiet in August, then scores in every September match.
    for match_id, day, month, goals in [
        (1, 10, 8, 0),
        (2, 17, 8, 0),
        (3, 24, 8, 0),
        (4, 7, 9, 1),
        (5, 14, 9, 2),
        (6, 21, 9, 1),
    ]:
        line = _line(match_id, day, "Barcelona", "Rival", 1, "Striker", "FW", 90, goals)
        lines.append(replace(line, played_on=date(2026, month, day), xg=0.6))
        # Always-good midfielder: one assist a game all season, same pace.
        mid = _line(match_id, day, "Barcelona", "Rival", 2, "Mid", "MC", 90)
        lines.append(replace(mid, played_on=date(2026, month, day), assists=1))
    # A sub who played 20 minutes once and scored: too little to rank.
    sub = _line(6, 21, "Barcelona", "Rival", 3, "Sub", "FW", 20, goals=1)
    lines.append(replace(sub, played_on=date(2026, 9, 21)))
    for match_id in {line.match_id for line in lines}:
        shots.save_rosters(match_id, [x for x in lines if x.match_id == match_id])
    return shots


def _hot(metric="goals_assists"):
    return HotPlayersUseCase(
        _repository(), competitions=["La Liga"], today=lambda: date(2026, 9, 30)
    ).execute("2026", days=30, metric=metric, limit=10)


def test_counts_only_the_last_days_and_skips_bit_part_players():
    board = _hot()

    assert [p.name for p in board.players] == ["Striker", "Mid"]
    striker = board.players[0]
    assert (striker.matches, striker.minutes, striker.goals) == (3, 270, 4)
    assert striker.xg == pytest.approx(1.8)
    assert board.window_start == date(2026, 8, 31)


def test_form_compares_the_window_with_his_earlier_pace():
    board = _hot(metric="form")

    striker, mid = board.players
    assert striker.name == "Striker"
    # 4 G+A in 270' now vs 0 in 270' before.
    assert striker.per90 == pytest.approx(4 / 3)
    assert striker.before_per90 == pytest.approx(0)
    # The midfielder keeps the same pace: no improvement.
    assert mid.per90 == pytest.approx(mid.before_per90)


def test_threat_ranks_by_expected_goals_and_assists():
    board = _hot(metric="threat")

    assert board.players[0].name == "Striker"
