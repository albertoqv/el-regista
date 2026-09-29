import csv
import io

from player_scouting.domain.season import Season
from player_scouting.infrastructure.fbref_kaggle.mapper import (
    normalize_competition,
    normalize_position,
    player_id_for,
    rows_to_results,
)

# Real column names from players_data_light-2026_2027.csv (basic metrics only).
BASIC_SEASON_CSV = """Rk,Player,Nation,Pos,Squad,Comp,Age,Born,MP,Starts,Min,90s,Gls,Ast,Sh,SoT,CrdY,CrdR,2CrdY,Fls,Fld,Int,TklW
1,Jude Bellingham,eng ENG,MF,Real Madrid,es La Liga,23,2003.0,7,7,610,6.8,3,2,14,7,1,0,0,9,15,3,6
2,Some Winger,fr FRA,"FW,MF",Club A,fr Ligue 1,25,2001.0,4,2,250,2.8,1,0,5,2,0,0,0,2,4,0,1
3,Some Winger,fr FRA,"FW,MF",Club B,fr Ligue 1,25,2001.0,3,3,270,3.0,2,1,6,3,1,1,1,1,2,1,0
4,Young Keeper,es ESP,GK,Club C,es La Liga,19,,1,1,90,1.0,,,,,,,,,,,
"""

# Real column names from players_data_light-2024_2025.csv (advanced metrics).
ADVANCED_SEASON_CSV = """Rk,Player,Nation,Pos,Squad,Comp,Age,Born,MP,Gls,Ast,Sh,SoT,CrdY,CrdR,Fls,Fld,Int,TklW,xG,Cmp,Att,KP,Succ,Att_stats_possession
1,Jude Bellingham,eng ENG,MF,Real Madrid,es La Liga,21,2003.0,31,9,8,50,20,6,1,30,70,15,40,11.4,1333,1548,42,41,75
"""


def _rows(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(csv_text)))


def test_player_id_is_deterministic_and_in_the_reserved_range():
    first = player_id_for("Jude Bellingham", 2003)
    second = player_id_for("Jude Bellingham", 2003)

    assert first == second
    assert 1_000_000_000 <= first < 2_147_483_647


def test_different_birth_years_give_different_ids():
    assert player_id_for("Pedro", 1997) != player_id_for("Pedro", 2002)


def test_normalize_competition_drops_the_country_prefix():
    assert normalize_competition("es La Liga") == "La Liga"
    assert normalize_competition("eng Premier League") == "Premier League"
    assert normalize_competition("Bundesliga") == "Bundesliga"


def test_normalize_position_uses_the_first_listed_role():
    assert normalize_position("FW,MF") == "Forward"
    assert normalize_position("GK") == "Goalkeeper"
    assert normalize_position("") is None


def test_maps_a_basic_season_row_to_a_player_season_result():
    results = rows_to_results(_rows(BASIC_SEASON_CSV), start_year=2026)

    jude = next(r for r in results if r.name == "Jude Bellingham")
    assert jude.player_id == player_id_for("Jude Bellingham", 2003)
    assert jude.position == "Midfielder"
    assert jude.birth_year == 2003
    assert jude.date_of_birth is None
    assert jude.season == Season("La Liga", "2026")
    stats = jude.statistics
    assert (stats.goals, stats.assists, stats.shots, stats.shots_on_target) == (
        3,
        2,
        14,
        7,
    )
    assert (stats.tackles_won, stats.interceptions) == (6, 3)
    assert (stats.fouls_committed, stats.fouls_won) == (9, 15)
    assert (stats.yellow_cards, stats.red_cards) == (1, 0)
    assert stats.expected_goals == 0.0
    assert stats.passes_attempted == 0


def test_sums_rows_of_a_player_transferred_within_the_same_league():
    results = rows_to_results(_rows(BASIC_SEASON_CSV), start_year=2026)

    winger = [r for r in results if r.name == "Some Winger"]
    assert len(winger) == 1
    assert winger[0].statistics.goals == 3
    assert winger[0].statistics.shots == 11
    assert winger[0].statistics.red_cards == 1


def test_empty_cells_and_missing_birth_year_become_zero_and_none():
    results = rows_to_results(_rows(BASIC_SEASON_CSV), start_year=2026)

    keeper = next(r for r in results if r.name == "Young Keeper")
    assert keeper.birth_year is None
    assert keeper.statistics.goals == 0
    assert keeper.position == "Goalkeeper"


def test_maps_advanced_metrics_when_the_season_has_them():
    results = rows_to_results(_rows(ADVANCED_SEASON_CSV), start_year=2024)

    stats = results[0].statistics
    assert stats.expected_goals == 11.4
    assert (stats.passes_completed, stats.passes_attempted) == (1333, 1548)
    assert stats.key_passes == 42
    assert (stats.dribbles_completed, stats.dribbles_attempted) == (41, 75)


def test_maps_team_and_minutes_played():
    results = rows_to_results(_rows(BASIC_SEASON_CSV), start_year=2026)

    jude = next(r for r in results if r.name == "Jude Bellingham")
    assert jude.team == "Real Madrid"
    assert jude.statistics.minutes_played == 610


def test_intra_league_transfer_lists_both_teams_and_sums_minutes():
    results = rows_to_results(_rows(BASIC_SEASON_CSV), start_year=2026)

    winger = next(r for r in results if r.name == "Some Winger")
    assert winger.team == "Club A, Club B"
    assert winger.statistics.minutes_played == 520
