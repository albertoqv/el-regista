from dataclasses import replace

from player_scouting.domain.career import CareerPoint, career_by_age
from player_scouting.domain.competitions import CompetitionLine

LEAGUE = CompetitionLine(
    competition="La Liga",
    kind="league",
    season_label="2024",
    team="FC Barcelona",
    appearances=35,
    goals=9,
    assists=15,
    minutes_played=2864,
    yellow_cards=0,
    red_cards=0,
)


def test_each_club_season_adds_up_its_competitions_at_the_age_he_had():
    champions = replace(
        LEAGUE,
        competition="Champions League",
        kind="continental",
        appearances=13,
        goals=5,
        assists=4,
        minutes_played=1103,
    )
    world_cup = replace(LEAGUE, competition="Mundial", kind="national", goals=7)

    [point] = career_by_age([LEAGUE, champions, world_cup], birth_year=2007)

    # National teams are not his club season; the age is the one he turns that year.
    assert point == CareerPoint(
        season_label="2024",
        age=17,
        appearances=48,
        goals=14,
        assists=19,
        minutes_played=3967,
        per90=round((14 + 19) * 90 / 3967, 3),
    )


def test_seasons_come_by_age_and_tiny_ones_are_left_out():
    older = replace(
        LEAGUE, season_label="2025", goals=16, assists=12, minutes_played=2270
    )
    cameo = replace(LEAGUE, season_label="2022", appearances=1, minutes_played=7)

    points = career_by_age([older, LEAGUE, cameo], birth_year=2007)

    assert [point.age for point in points] == [17, 18]


def test_without_a_birth_year_there_is_no_curve():
    assert career_by_age([LEAGUE], birth_year=None) == []
