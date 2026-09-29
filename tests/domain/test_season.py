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
