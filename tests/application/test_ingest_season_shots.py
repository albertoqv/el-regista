from datetime import date

from player_scouting.application.ports import MatchRef
from player_scouting.application.use_cases.ingest_season_shots import (
    IngestSeasonShotsUseCase,
)
from player_scouting.domain.shots import Shot
from tests.application.doubles import FakeShotProvider, InMemoryShotRepository


def _match(match_id: int, day: int) -> MatchRef:
    return MatchRef(match_id, "La Liga", "2026", date(2026, 8, day), "Home", "Away")


def _goal(match_id: int, minute: int, home: bool) -> Shot:
    return Shot(
        shot_id=match_id * 1000 + minute,
        match_id=match_id,
        understat_player_id=7,
        player_name="Scorer",
        minute=minute,
        result="Goal",
        x=0.9,
        y=0.5,
        xg=0.4,
        situation="OpenPlay",
        shot_type="LeftFoot",
        home=home,
        assisted_by=None,
    )


def _provider() -> FakeShotProvider:
    return FakeShotProvider(
        matches=[_match(1, 15), _match(2, 16), _match(3, 17)],
        shots={
            1: [_goal(1, 10, True), _goal(1, 80, True)],
            2: [_goal(2, 5, False)],
            3: [],
        },
    )


def test_ingests_only_matches_it_does_not_have_yet_and_marks_decisive_goals():
    repository = InMemoryShotRepository()
    repository.save_match(_match(1, 15), [])
    provider = _provider()

    summary = IngestSeasonShotsUseCase(
        provider, repository, pause=lambda s: None
    ).execute(2026, limit=10)

    assert provider.requested == [2, 3]
    assert summary.matches == 2
    assert summary.shots == 1
    assert summary.remaining == 0
    [goal] = repository.shots_of(2)
    assert goal.decisive


def test_respects_the_batch_limit_oldest_first():
    repository = InMemoryShotRepository()
    provider = _provider()

    summary = IngestSeasonShotsUseCase(
        provider, repository, pause=lambda s: None
    ).execute(2026, limit=2)

    assert provider.requested == [1, 2]
    assert summary.remaining == 1
    assert [s.decisive for s in repository.shots_of(1)] == [True, False]
