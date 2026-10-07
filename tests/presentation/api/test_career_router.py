from dataclasses import replace
from datetime import date

from fastapi.testclient import TestClient

from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
from player_scouting.presentation.api.dependencies import (
    get_competition_stats_repository,
    get_player_repository,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    InMemoryCompetitionStatsRepository,
    InMemoryPlayerRepository,
)

LEAGUE = CompetitionLine(
    competition="La Liga",
    kind="league",
    season_label="2024",
    team="FC Barcelona",
    appearances=30,
    goals=9,
    assists=9,
    minutes_played=1800,
    yellow_cards=0,
    red_cards=0,
)


def test_a_players_career_by_age_next_to_his_positions_level():
    players = InMemoryPlayerRepository()
    players.save_player(Player(7, "Lamine Yamal", "Forward", date(2007, 7, 13)))
    players.save_player(Player(8, "Another", "Forward", date(2007, 1, 1)))
    competitions = InMemoryCompetitionStatsRepository(players)
    competitions.save_competition_lines(
        {7: [LEAGUE], 8: [replace(LEAGUE, goals=0, assists=9)]}
    )
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: players
    app.dependency_overrides[get_competition_stats_repository] = lambda: competitions

    body = TestClient(app).get("/players/7/career").json()

    assert body["position"] == "Forward"
    [point] = body["points"]
    assert (point["age"], point["season_label"], point["per90"]) == (17, "2024", 0.9)
    [age] = body["benchmark"]
    assert (age["age"], age["players"]) == (17, 2)
    assert age["per90"] == round((18 + 9) * 90 / 3600, 3)


def test_an_unknown_player_has_no_career():
    app = create_app()
    app.dependency_overrides[get_player_repository] = InMemoryPlayerRepository
    app.dependency_overrides[get_competition_stats_repository] = (
        InMemoryCompetitionStatsRepository
    )

    assert TestClient(app).get("/players/404/career").status_code == 404
