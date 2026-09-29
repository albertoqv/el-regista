from player_scouting.presentation.api.season_year import extract_season_year


def test_extracts_a_plain_year():
    assert extract_season_year("2023") == 2023


def test_extracts_the_first_year_from_a_slash_separated_label():
    assert extract_season_year("1983/1984") == 1983


def test_returns_none_for_a_label_without_digits():
    assert extract_season_year("FIFA World Cup") is None


def test_returns_none_for_an_empty_label():
    assert extract_season_year("") is None
