import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.application.ports import MatchRef
from player_scouting.domain.entities import Player
from player_scouting.domain.shots import Shot
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)
from player_scouting.infrastructure.persistence.sqlalchemy_shot_repository import (
    MINIMUM_SHOTS_FOR_RATES,
    SqlAlchemyShotRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(DATABASE_URL is None, reason="DATABASE_URL is not set")

MATCH = MatchRef(1, "La Liga", "2026", date(2026, 8, 15), "Barcelona", "Getafe")
OTHER_LEAGUE = MatchRef(2, "Serie A", "2026", date(2026, 8, 16), "Inter", "Roma")


@pytest.fixture
def session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


def _shot(shot_id, understat_id, minute, result="Goal", home=True, **extra) -> Shot:
    values = dict(
        shot_id=shot_id,
        match_id=extra.pop("match_id", 1),
        understat_player_id=understat_id,
        player_name=f"U{understat_id}",
        minute=minute,
        result=result,
        x=0.9,
        y=0.5,
        xg=0.3,
        situation="OpenPlay",
        shot_type="RightFoot",
        home=home,
        assisted_by=None,
        decisive=False,
    )
    values.update(extra)
    return Shot(**values)


def _seed_players(session) -> None:
    players = SqlAlchemyPlayerRepository(session)
    for player_id, name, understat_id in (
        (1, "Raphinha", 101),
        (2, "Lamine Yamal", 102),
        (3, "Lautaro Martínez", 103),
    ):
        players.save_player(Player(player_id, name, "Forward", None, birth_year=2000))
        players.set_understat_id(player_id, understat_id)


def test_saves_a_match_and_remembers_it(session):
    repository = SqlAlchemyShotRepository(session)

    repository.save_match(MATCH, [_shot(1, 101, 10)])
    repository.save_match(MATCH, [_shot(1, 101, 10), _shot(2, 101, 20)])

    assert repository.known_match_ids("2026") == {1}
    assert repository.known_match_ids("2025") == set()


def test_late_and_decisive_goal_leaders(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    repository.save_match(
        MATCH,
        [
            _shot(1, 101, 80, decisive=True),
            _shot(2, 101, 88),
            _shot(3, 102, 77, decisive=True),
            _shot(4, 102, 30, decisive=True),
            _shot(5, 102, 85, result="SavedShot"),
        ],
    )
    repository.save_match(OTHER_LEAGUE, [_shot(6, 103, 90, match_id=2)])

    late = repository.list_shot_leaders("2026", "late_goals", 5)
    decisive = repository.list_shot_leaders("2026", "decisive_goals", 5)
    late_decisive = repository.list_shot_leaders("2026", "late_decisive_goals", 5)
    in_serie_a = repository.list_shot_leaders("2026", "late_goals", 5, "Serie A")

    assert [(leader.player.name, leader.value) for leader in late] == [
        ("Raphinha", 2),
        ("Lamine Yamal", 1),
        ("Lautaro Martínez", 1),
    ]
    assert late[0].team == "Barcelona"
    assert [(leader.player.name, leader.value) for leader in decisive][0] == (
        "Lamine Yamal",
        2,
    )
    assert [leader.player.name for leader in late_decisive] == [
        "Lamine Yamal",
        "Raphinha",
    ]
    assert [leader.player.name for leader in in_serie_a] == ["Lautaro Martínez"]


def test_headers_outside_the_box_and_set_pieces(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    repository.save_match(
        MATCH,
        [
            _shot(1, 101, 10, shot_type="Head"),
            _shot(2, 102, 20, x=0.75),
            _shot(3, 102, 30, situation="DirectFreekick", x=0.76),
        ],
    )

    headed = repository.list_shot_leaders("2026", "headed_goals", 5)
    long_range = repository.list_shot_leaders("2026", "outside_box_goals", 5)
    set_piece = repository.list_shot_leaders("2026", "set_piece_goals", 5)

    assert [leader.player.name for leader in headed] == ["Raphinha"]
    assert [(leader.player.name, leader.value) for leader in long_range] == [
        ("Lamine Yamal", 2)
    ]
    assert [leader.player.name for leader in set_piece] == ["Lamine Yamal"]


def test_finishing_is_non_penalty_goals_minus_expected_goals(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    repository.save_match(
        MATCH,
        [
            _shot(1, 101, 10, xg=0.1),
            _shot(2, 101, 20, xg=0.2, result="MissedShot"),
            _shot(3, 101, 30, xg=0.76, situation="Penalty"),
        ],
    )

    [leader] = repository.list_shot_leaders("2026", "finishing", 5)

    assert leader.value == pytest.approx(0.7)
    assert (leader.goals, leader.shots) == (1, 2)


def test_rates_need_a_minimum_number_of_shots(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    shots = [
        _shot(i, 101, i, xg=0.2, result="MissedShot")
        for i in range(1, MINIMUM_SHOTS_FOR_RATES + 1)
    ]
    shots.append(_shot(100, 102, 5, xg=0.9))
    repository.save_match(MATCH, shots)

    leaders = repository.list_shot_leaders("2026", "npxg_per_shot", 5)

    assert [(leader.player.name, round(leader.value, 2)) for leader in leaders] == [
        ("Raphinha", 0.2)
    ]


def test_player_shots_carry_match_context(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    repository.save_match(MATCH, [_shot(1, 101, 10), _shot(2, 102, 11, home=False)])

    [shot] = repository.list_player_shots(1)
    [away] = repository.list_player_shots(2, "2026")

    assert shot.shot.minute == 10
    assert (shot.team, shot.opponent) == ("Barcelona", "Getafe")
    assert (away.team, away.opponent) == ("Getafe", "Barcelona")
    assert shot.played_on == date(2026, 8, 15)
    assert repository.list_player_shots(1, "2025") == []


def test_partnerships_count_assisted_goals(session):
    _seed_players(session)
    repository = SqlAlchemyShotRepository(session)
    repository.save_match(
        MATCH,
        [
            _shot(1, 101, 10, assisted_by="Lamine Yamal"),
            _shot(2, 101, 20, assisted_by="Lamine Yamal"),
            _shot(3, 102, 30, assisted_by="Pedri"),
            _shot(4, 101, 40, assisted_by="Lamine Yamal", result="SavedShot"),
        ],
    )

    [best, second] = repository.list_partnerships("2026", 5)

    assert (best.scorer.name, best.assister_name, best.goals) == (
        "Raphinha",
        "Lamine Yamal",
        2,
    )
    assert best.assister is not None and best.assister.player_id == 2
    assert best.team == "Barcelona"
    assert second.assister is None
