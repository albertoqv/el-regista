from datetime import date

from player_scouting.domain.season import Season
from player_scouting.infrastructure.api_football.mapper import (
    to_player_season_result,
)

# Shape captured from a real call to https://v3.football.api-sports.io/players
# (league=140, season=2023, search=Bellingham) during an earlier session.
PLAYER_INFO = {
    "id": 129718,
    "name": "J. Bellingham",
    "birth": {"date": "2003-06-29"},
    "photo": "https://media.api-sports.io/football/players/129718.png",
}
STATS_BLOCK = {
    "team": {"id": 541, "name": "Real Madrid"},
    "league": {"id": 140, "name": "La Liga", "season": 2023},
    "games": {"position": "Midfielder"},
    "shots": {"total": 49, "on": 35},
    "goals": {"total": 19, "assists": 6},
    "passes": {"total": 1500, "key": 48, "accuracy": 48},
    "tackles": {"total": 43, "interceptions": 21},
    "dribbles": {"attempts": 85, "success": 50},
    "fouls": {"drawn": 72, "committed": 32},
    "cards": {"yellow": 5, "yellowred": None, "red": 1},
}


def test_maps_a_real_shaped_entry_to_a_player_season_result():
    result = to_player_season_result(PLAYER_INFO, STATS_BLOCK, season_year=2023)

    assert result.player_id == 129718
    assert result.name == "J. Bellingham"
    assert result.position == "Midfielder"
    assert result.date_of_birth == date(2003, 6, 29)
    assert result.season == Season("La Liga", "2023")
    assert (
        result.photo_url == "https://media.api-sports.io/football/players/129718.png"
    )


def test_maps_the_statistics_block_including_derived_passes_completed():
    result = to_player_season_result(PLAYER_INFO, STATS_BLOCK, season_year=2023)

    stats = result.statistics
    assert stats.goals == 19
    assert stats.assists == 6
    assert stats.shots == 49
    assert stats.shots_on_target == 35
    assert stats.passes_attempted == 1500
    assert stats.passes_completed == 720  # 1500 * 48%
    assert stats.key_passes == 48
    assert stats.dribbles_attempted == 85
    assert stats.dribbles_completed == 50
    assert stats.tackles_won == 43
    assert stats.interceptions == 21
    assert stats.fouls_committed == 32
    assert stats.fouls_won == 72
    assert stats.yellow_cards == 5
    assert stats.red_cards == 1


def test_sums_red_and_second_yellow_cards_into_red_cards():
    player_info = {"id": 1, "name": "Some Player", "birth": {"date": "1995-01-01"}}
    stats_block = {
        "league": {"name": "Premier League", "season": 2023},
        "games": {"position": "Defender"},
        "shots": {},
        "goals": {},
        "passes": {},
        "tackles": {},
        "dribbles": {},
        "fouls": {},
        "cards": {"yellow": 0, "yellowred": 1, "red": 1},
    }

    result = to_player_season_result(player_info, stats_block, season_year=2023)

    assert result.statistics.red_cards == 2


def test_falls_back_to_unknown_league_and_the_given_season_year_when_missing():
    player_info = {"id": 1, "name": "Some Player", "birth": {"date": "1995-01-01"}}
    stats_block = {
        "games": {},
        "shots": {},
        "goals": {},
        "passes": {},
        "tackles": {},
        "dribbles": {},
        "fouls": {},
        "cards": {},
    }

    result = to_player_season_result(player_info, stats_block, season_year=2023)

    assert result.season == Season("Unknown", "2023")
