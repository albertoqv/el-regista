from dataclasses import replace
from datetime import date, datetime

import pytest

from player_scouting.application.ports import PredictionSnapshot
from player_scouting.application.use_cases.track_record import (
    SnapshotPredictionsUseCase,
    TrackRecordUseCase,
    week_start,
)
from tests.application.doubles import InMemoryPredictionLog
from tests.application.test_match_insights import _stats_repository
from tests.application.test_team_analytics import _repository as team_repository


def _snapshot(match_id, model, market=None, kickoff=datetime(2026, 9, 29, 21)):
    return PredictionSnapshot(
        match_id=match_id,
        competition="La Liga",
        season_label="2026",
        kickoff=kickoff,
        home_team="Getafe",
        away_team="Barcelona",
        made_at=datetime(2026, 9, 25, 6),
        model=model,
        market=market,
        over_2_5=0.4,
    )


def test_snapshots_store_upcoming_forecasts_before_kickoff():
    log = InMemoryPredictionLog()

    saved = SnapshotPredictionsUseCase(
        team_repository(),
        _stats_repository(),
        log,
        now=lambda: datetime(2026, 10, 1, 6),
    ).execute(days=7)

    # Only the 4 Oct fixture is within a week; the December one waits.
    assert saved == 1
    [snapshot] = log.list_snapshots()
    assert snapshot.match_id == 6
    assert sum(snapshot.model) == pytest.approx(1.0)
    assert snapshot.market is not None and sum(snapshot.market) == pytest.approx(1.0)
    assert 0 < snapshot.over_2_5 < 1
    assert snapshot.made_at == datetime(2026, 10, 1, 6)


def test_a_later_snapshot_replaces_the_earlier_one_but_never_after_kickoff():
    log = InMemoryPredictionLog()
    log.save_snapshot(_snapshot(6, (0.2, 0.3, 0.5), kickoff=datetime(2026, 10, 4, 21)))

    SnapshotPredictionsUseCase(
        team_repository(), _stats_repository(), log, now=lambda: datetime(2026, 10, 3)
    ).execute(days=7)
    refreshed = log.list_snapshots()[0]
    # After kickoff there is nothing upcoming to snapshot: the log stays frozen.
    SnapshotPredictionsUseCase(
        team_repository(), _stats_repository(), log, now=lambda: datetime(2026, 10, 5)
    ).execute(days=7)

    assert refreshed.made_at == datetime(2026, 10, 3)
    assert log.list_snapshots() == [refreshed]


def test_week_start_is_the_monday():
    assert week_start(date(2026, 10, 4)) == date(2026, 9, 28)
    assert week_start(date(2026, 9, 28)) == date(2026, 9, 28)


def test_live_record_scores_only_logged_forecasts_against_real_results():
    log = InMemoryPredictionLog()
    # Match 5 (29 Sep): Getafe 0-1 Barcelona.
    log.save_snapshot(_snapshot(5, (0.2, 0.25, 0.55), market=(0.25, 0.3, 0.45)))
    # Match 6 has not been played yet: pending, not scored.
    log.save_snapshot(_snapshot(6, (0.7, 0.2, 0.1), kickoff=datetime(2026, 10, 4, 21)))

    record = TrackRecordUseCase(team_repository(), log).execute("2026")

    assert record.live_total.matches == 1
    assert record.live_total.hits == 1
    assert record.live_total.brier == pytest.approx(0.2**2 + 0.25**2 + 0.45**2)
    assert record.live_total.market_matches == 1
    assert record.live_total.market_hits == 1
    assert record.pending == 1
    [week] = record.live_weeks
    assert week.week_start == date(2026, 9, 28)
    [latest] = record.live_recent
    assert (latest.match_id, latest.home_goals, latest.away_goals) == (5, 0, 1)
    assert latest.model_hit


def test_confident_picks_are_counted_apart():
    log = InMemoryPredictionLog()
    log.save_snapshot(_snapshot(5, (0.1, 0.2, 0.7)))  # right and confident
    log.save_snapshot(replace(_snapshot(4, (0.65, 0.2, 0.15))))  # 1-1: wrong

    total = TrackRecordUseCase(team_repository(), log).execute("2026").live_total

    assert (total.matches, total.hits) == (2, 1)
    assert (total.confident, total.confident_hits) == (2, 1)


def test_the_season_is_rebuilt_week_by_week_without_looking_ahead():
    record = TrackRecordUseCase(
        team_repository(), InMemoryPredictionLog(), minimum_history=1
    ).execute("2026")

    # Matches 2..5 have at least one earlier match to learn from.
    assert record.rebuilt_total.matches == 4
    assert sum(w.matches for w in record.rebuilt_weeks) == 4
    assert [w.week_start for w in record.rebuilt_weeks] == sorted(
        w.week_start for w in record.rebuilt_weeks
    )
    assert 0 <= record.rebuilt_total.brier <= 2
