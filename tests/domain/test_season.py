from player_scouting.domain.season import Season


def test_season_stores_its_data():
    season = Season("La Liga", "2023")

    assert season.competition == "La Liga"
    assert season.label == "2023"


def test_two_seasons_with_the_same_data_are_equal():
    assert Season("La Liga", "2023") == Season("La Liga", "2023")


def test_two_seasons_with_different_data_are_not_equal():
    assert Season("La Liga", "2023") != Season("La Liga", "2024")


def test_season_is_hashable():
    seasons = {Season("La Liga", "2023"), Season("La Liga", "2023")}

    assert len(seasons) == 1


def test_start_year_of_a_plain_year_label():
    assert Season("La Liga", "2023").start_year == 2023


def test_start_year_takes_the_first_year_of_a_slash_label():
    assert Season("Copa del Rey", "1983/1984").start_year == 1983


def test_start_year_is_none_when_the_label_has_no_year():
    assert Season("FIFA World Cup", "Final").start_year is None
