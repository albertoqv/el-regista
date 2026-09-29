import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.persistence.models import Base
from player_scouting.infrastructure.persistence.sqlalchemy_player_repository import (
    SqlAlchemyPlayerRepository,
)

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    DATABASE_URL is None,
    reason="DATABASE_URL is not set; start Postgres with `docker compose up -d db`",
)

LA_LIGA_2023 = Season("La Liga", "2023")
PREMIER_LEAGUE_2023 = Season("Premier League", "2023")


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


def test_saves_and_retrieves_a_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    player = Player(1, "Player One", "Forward", date(1995, 1, 1))

    repository.save_player(player)

    assert repository.get_player(1) == player


def test_saves_and_retrieves_a_players_photo(session):
    repository = SqlAlchemyPlayerRepository(session)
    player = Player(
        1,
        "Player One",
        "Forward",
        date(1995, 1, 1),
        photo_url="https://media.api-sports.io/football/players/1.png",
    )

    repository.save_player(player)

    assert (
        repository.get_player(1).photo_url
        == "https://media.api-sports.io/football/players/1.png"
    )


def test_a_player_without_a_photo_has_none(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    assert repository.get_player(1).photo_url is None


def test_get_player_returns_none_for_a_missing_player(session):
    repository = SqlAlchemyPlayerRepository(session)

    assert repository.get_player(999) is None


def test_saves_and_retrieves_a_players_preferred_foot(session):
    repository = SqlAlchemyPlayerRepository(session)
    player = Player(
        1, "Player One", "Forward", date(1995, 1, 1), preferred_foot="right"
    )

    repository.save_player(player)

    assert repository.get_player(1).preferred_foot == "right"


def test_a_player_without_a_preferred_foot_has_none(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    assert repository.get_player(1).preferred_foot is None


def test_saves_and_lists_market_value_history(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    points = [
        MarketValuePoint(date(2019, 10, 17), 2_500_000, "Birmingham City"),
        MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid"),
    ]

    repository.save_market_value_history(1, points)

    assert repository.list_market_value_history(1) == points


def test_saving_market_value_history_again_replaces_the_previous_one(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_market_value_history(
        1, [MarketValuePoint(date(2019, 10, 17), 2_500_000, "Birmingham City")]
    )

    repository.save_market_value_history(
        1, [MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid")]
    )

    history = repository.list_market_value_history(1)
    assert history == [MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid")]


def test_market_value_history_is_empty_for_a_player_with_none(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    assert repository.list_market_value_history(1) == []


def test_saves_and_retrieves_season_statistics(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(10, 5))

    assert repository.get_season_statistics(1, LA_LIGA_2023) == Statistics(10, 5)


def test_get_season_statistics_returns_none_when_not_ingested(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    assert repository.get_season_statistics(1, LA_LIGA_2023) is None


def test_saving_the_same_season_twice_updates_it_instead_of_duplicating(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(10, 5))

    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(20, 15))

    assert repository.get_season_statistics(1, LA_LIGA_2023) == Statistics(20, 15)
    assert repository.list_seasons_for_player(1) == [LA_LIGA_2023]


def test_saves_and_retrieves_extended_metrics(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    statistics = Statistics(
        goals=10,
        assists=5,
        shots=20,
        shots_on_target=8,
        expected_goals=6.7,
        passes_completed=300,
        passes_attempted=350,
        key_passes=12,
        dribbles_completed=15,
        dribbles_attempted=25,
        tackles_won=4,
        interceptions=3,
        fouls_committed=6,
        fouls_won=9,
        yellow_cards=2,
        red_cards=0,
    )

    repository.save_season_statistics(1, LA_LIGA_2023, statistics)

    assert repository.get_season_statistics(1, LA_LIGA_2023) == statistics


def test_lists_every_season_a_player_has_statistics_for(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(10, 5))
    repository.save_season_statistics(1, PREMIER_LEAGUE_2023, Statistics(3, 3))

    seasons = repository.list_seasons_for_player(1)

    assert set(seasons) == {LA_LIGA_2023, PREMIER_LEAGUE_2023}


def test_career_statistics_sum_every_season(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(10, 5))
    repository.save_season_statistics(1, PREMIER_LEAGUE_2023, Statistics(3, 3))

    career = repository.get_career_statistics(1)

    assert career.goals == 13
    assert career.assists == 8


def test_career_statistics_are_zero_for_a_player_with_no_seasons(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))

    career = repository.get_career_statistics(1)

    assert career == Statistics(0, 0)


def test_lists_every_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_player(Player(2, "Player Two", "Midfielder", date(1996, 1, 1)))

    players = repository.list_players()

    assert {player.player_id for player in players} == {1, 2}


def test_lists_every_season_statistics_record_across_all_players(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", date(1995, 1, 1)))
    repository.save_player(Player(2, "Player Two", "Midfielder", date(1996, 1, 1)))
    repository.save_season_statistics(1, LA_LIGA_2023, Statistics(10, 5))
    repository.save_season_statistics(2, PREMIER_LEAGUE_2023, Statistics(3, 3))

    entries = repository.list_all_season_statistics()

    seasons_by_player = {player.player_id: season for player, season, _ in entries}
    assert seasons_by_player == {1: LA_LIGA_2023, 2: PREMIER_LEAGUE_2023}
