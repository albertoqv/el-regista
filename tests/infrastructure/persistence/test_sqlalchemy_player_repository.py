import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import AdvancedStatistics, Statistics
from player_scouting.infrastructure.persistence.models import Base, PlayerModel
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


def test_saves_a_player_with_only_a_birth_year(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Player One", "Forward", None, birth_year=2003))

    player = repository.get_player(1)

    assert player.date_of_birth is None
    assert player.birth_year == 2003


def _seed_summaries(repository: SqlAlchemyPlayerRepository) -> None:
    repository.save_player(Player(1, "Historic Striker", "Forward", date(1960, 1, 1)))
    repository.save_season_statistics(
        1, Season("Copa del Rey", "1983/1984"), Statistics(40, 1)
    )
    repository.save_player(
        Player(2, "Current Winger", "Forward", None, birth_year=2001)
    )
    repository.save_season_statistics(2, Season("La Liga", "2026"), Statistics(3, 9))
    repository.save_player(
        Player(3, "Current Striker", "Forward", None, birth_year=1998)
    )
    repository.save_season_statistics(3, Season("La Liga", "2025"), Statistics(20, 2))
    repository.save_season_statistics(3, Season("La Liga", "2026"), Statistics(7, 1))
    repository.save_player(Player(4, "No Seasons Yet", "Defender", None))


def test_summaries_sorted_by_recency_then_contribution(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_summaries(repository)

    summaries = repository.search_player_summaries(None, "recent", 10)

    assert [s.player.player_id for s in summaries] == [3, 2, 1, 4]
    assert summaries[0].latest_season_year == 2026
    assert summaries[0].career.goals == 27
    assert summaries[2].latest_season_year == 1983
    assert summaries[3].latest_season_year is None
    assert summaries[3].career == Statistics(0, 0)


def test_summaries_sorted_by_goals_and_by_assists(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_summaries(repository)

    by_goals = repository.search_player_summaries(None, "goals", 2)
    by_assists = repository.search_player_summaries(None, "assists", 1)

    assert [s.player.player_id for s in by_goals] == [1, 3]
    assert [s.player.player_id for s in by_assists] == [2]


def test_summaries_filter_by_name_case_insensitively(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_summaries(repository)

    summaries = repository.search_player_summaries("current", "recent", 10)

    assert {s.player.player_id for s in summaries} == {2, 3}


YAMAL_ADVANCED = AdvancedStatistics(
    expected_goals=6.08,
    expected_assists=4.08,
    key_passes=27,
    xg_chain=9.5,
    xg_buildup=2.1,
)
LA_LIGA_2026 = Season("La Liga", "2026")


def _seed_yamal(repository: SqlAlchemyPlayerRepository) -> None:
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_season_statistics(
        1,
        LA_LIGA_2026,
        Statistics(7, 4, key_passes=0, minutes_played=598),
        team="Barcelona",
    )


def test_season_entries_include_team_and_minutes(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)

    [entry] = repository.list_season_entries(LA_LIGA_2026)

    assert entry.player.player_id == 1
    assert entry.team == "Barcelona"
    assert entry.statistics.minutes_played == 598


def test_returns_the_team_of_a_player_season(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)

    assert repository.get_season_team(1, LA_LIGA_2026) == "Barcelona"
    assert repository.get_season_team(1, Season("La Liga", "1999")) is None


def test_advanced_metrics_are_merged_into_every_statistics_read(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)

    repository.save_season_advanced(1, LA_LIGA_2026, YAMAL_ADVANCED)

    season = repository.get_season_statistics(1, LA_LIGA_2026)
    career = repository.get_career_statistics(1)
    [(_, _, listed)] = repository.list_all_season_statistics()
    [summary] = repository.search_player_summaries(None, "recent", 5)
    for stats in (season, career, listed, summary.career):
        assert stats.expected_goals == 6.08
        assert stats.expected_assists == 4.08
        assert stats.key_passes == 27
        assert stats.xg_chain == 9.5
        assert stats.goals == 7


def test_a_later_basic_refresh_keeps_the_advanced_metrics(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)
    repository.save_season_advanced(1, LA_LIGA_2026, YAMAL_ADVANCED)

    repository.save_season_statistics(
        1, LA_LIGA_2026, Statistics(8, 4, minutes_played=688), team="Barcelona"
    )

    stats = repository.get_season_statistics(1, LA_LIGA_2026)
    assert stats.goals == 8
    assert stats.expected_goals == 6.08


def test_stores_the_understat_id(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)

    repository.set_understat_id(1, 11500)

    stored = session.get(PlayerModel, 1)
    assert stored.understat_id == 11500


def test_pending_enrichment_is_ranked_and_excludes_checked_players(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)
    repository.save_player(Player(2, "Bench Player", "Defender", None, birth_year=2001))
    repository.save_season_statistics(2, LA_LIGA_2026, Statistics(0, 0))

    assert [p.player_id for p in repository.list_players_pending_enrichment(5)] == [
        1,
        2,
    ]

    repository.mark_enrichment_checked(1)

    assert [p.player_id for p in repository.list_players_pending_enrichment(5)] == [2]


def test_season_leaders_are_ranked_by_a_metric_across_competitions(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)
    repository.save_player(Player(2, "Harry Kane", "Forward", None, birth_year=1993))
    repository.save_season_statistics(
        2,
        Season("Bundesliga", "2026"),
        Statistics(12, 2, minutes_played=630),
        team="Bayern Munich",
    )
    repository.save_player(Player(3, "Old Star", "Forward", None, birth_year=1980))
    repository.save_season_statistics(3, Season("La Liga", "2010"), Statistics(40, 10))
    repository.save_season_advanced(1, LA_LIGA_2026, YAMAL_ADVANCED)

    by_goals = repository.list_season_leaders("2026", "goals", 5)
    by_xa = repository.list_season_leaders("2026", "expected_assists", 5)
    in_la_liga = repository.list_season_leaders("2026", "goals", 5, "La Liga")

    assert [leader.player.name for leader in by_goals] == [
        "Harry Kane",
        "Lamine Yamal",
    ]
    assert by_goals[0].team == "Bayern Munich"
    assert by_goals[0].season == Season("Bundesliga", "2026")
    assert by_xa[0].statistics.expected_assists == 4.08
    assert [leader.player.name for leader in in_la_liga] == ["Lamine Yamal"]


def test_season_records_for_some_labels_include_the_team(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)
    repository.save_season_statistics(1, Season("La Liga", "2010"), Statistics(1, 1))

    [record] = repository.list_season_records(["2026"])

    assert record.player.name == "Lamine Yamal"
    assert record.season == LA_LIGA_2026
    assert record.team == "Barcelona"


def test_latest_market_value_of_every_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    _seed_yamal(repository)
    repository.save_market_value_history(
        1,
        [
            MarketValuePoint(date(2025, 1, 1), 150_000_000, "Barcelona"),
            MarketValuePoint(date(2026, 6, 1), 200_000_000, "Barcelona"),
        ],
    )

    latest = repository.latest_market_values()

    assert latest == {1: MarketValuePoint(date(2026, 6, 1), 200_000_000, "Barcelona")}


def test_groups_players_that_share_an_understat_id(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Che Adams", "Forward", None, birth_year=1996))
    repository.save_player(Player(2, "Ché Adams", "Forward", None, birth_year=1996))
    repository.save_player(Player(3, "Other", "Forward", None, birth_year=1996))
    for player_id in (1, 2):
        repository.set_understat_id(player_id, 555)
    repository.set_understat_id(3, 777)

    assert repository.list_duplicate_groups() == [[1, 2]]


def test_merging_moves_seasons_and_values_to_the_kept_player(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Che Adams", "Forward", None, birth_year=1996))
    repository.save_player(
        Player(2, "Ché Adams", "Forward", date(1996, 7, 13), birth_year=1996)
    )
    repository.save_season_statistics(1, Season("Serie A", "2024"), Statistics(9, 1))
    repository.save_season_statistics(1, Season("Serie A", "2026"), Statistics(1, 0))
    repository.save_season_statistics(2, Season("Serie A", "2026"), Statistics(2, 0))
    repository.save_season_advanced(1, Season("Serie A", "2024"), YAMAL_ADVANCED)
    repository.save_market_value_history(
        1, [MarketValuePoint(date(2025, 1, 1), 5_000_000, "Torino")]
    )

    repository.merge_players(keep=2, remove=1)

    assert repository.get_player(1) is None
    seasons = {s.label for s in repository.list_seasons_for_player(2)}
    assert seasons == {"2024", "2026"}
    # The kept player's own row wins when both have the same season.
    assert repository.get_season_statistics(2, Season("Serie A", "2026")).goals == 2
    assert (
        repository.get_season_statistics(2, Season("Serie A", "2024")).xg_chain == 9.5
    )
    assert repository.list_market_value_history(2)[0].amount_eur == 5_000_000


def test_stores_height_detailed_position_and_transfermarkt_id(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(
        Player(
            1,
            "Lamine Yamal",
            "Forward",
            date(2007, 7, 13),
            height_cm=183,
            detailed_position="Right Winger",
        )
    )
    repository.set_transfermarkt_id(1, 937958)

    player = repository.get_player(1)

    assert (player.height_cm, player.detailed_position) == (183, "Right Winger")
    assert repository.transfermarkt_index() == {937958: 1}


def test_finds_players_by_their_understat_ids(session):
    repository = SqlAlchemyPlayerRepository(session)
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.set_understat_id(1, 11500)

    found = repository.find_by_understat_ids([11500, 999])

    assert list(found) == [11500] and found[11500].name == "Lamine Yamal"
