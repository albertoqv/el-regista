from dataclasses import replace

from fastapi.testclient import TestClient

from player_scouting.application.ports import DatasetCompetitionRow
from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
from player_scouting.presentation.api.dependencies import (
    get_competition_stats_repository,
    get_player_repository,
    get_transfermarkt_dataset_provider,
)
from player_scouting.presentation.api.main import create_app
from tests.application.doubles import (
    InMemoryCompetitionStatsRepository,
    InMemoryPlayerRepository,
)

CHAMPIONS = CompetitionLine(
    competition="Champions League",
    kind="continental",
    season_label="2025",
    team="FC Barcelona",
    appearances=10,
    goals=6,
    assists=4,
    minutes_played=874,
    yellow_cards=1,
    red_cards=0,
)


class FakeDataset:
    def competition_rows(self, since):
        return [DatasetCompetitionRow(937958, CHAMPIONS)]


def _client(competitions: InMemoryCompetitionStatsRepository) -> TestClient:
    players = InMemoryPlayerRepository()
    players.save_player(Player(7, "Lamine Yamal", "Forward", None, birth_year=2007))
    players.set_transfermarkt_id(7, 937958)
    app = create_app()
    app.dependency_overrides[get_player_repository] = lambda: players
    app.dependency_overrides[get_competition_stats_repository] = lambda: competitions
    app.dependency_overrides[get_transfermarkt_dataset_provider] = FakeDataset
    return TestClient(app)


def test_a_players_lines_per_competition_newest_first():
    competitions = InMemoryCompetitionStatsRepository()
    cup = replace(
        CHAMPIONS, competition="Copa del Rey", kind="cup", season_label="2024"
    )
    competitions.save_competition_lines({7: [cup, CHAMPIONS]})

    body = _client(competitions).get("/players/7/competitions").json()

    assert [line["competition"] for line in body] == [
        "Champions League",
        "Copa del Rey",
    ]
    assert body[0] == {
        "competition": "Champions League",
        "kind": "continental",
        "season_label": "2025",
        "team": "FC Barcelona",
        "appearances": 10,
        "goals": 6,
        "assists": 4,
        "minutes_played": 874,
        "yellow_cards": 1,
        "red_cards": 0,
    }


def test_the_refresh_loads_the_dataset_competitions():
    competitions = InMemoryCompetitionStatsRepository()

    response = _client(competitions).post(
        "/ingestion/transfermarkt-dataset/competitions"
    )

    assert response.json()["ingested"] == 1
    assert competitions.list_competition_lines(7) == [CHAMPIONS]


def test_lines_read_from_transfermarkt_pages_are_stored_by_transfermarkt_id():
    competitions = InMemoryCompetitionStatsRepository()
    row = {
        "transfermarkt_id": 937958,
        "team": "FC Barcelona",
        "appearances": 2,
        "goals": 1,
        "assists": 1,
        "minutes_played": 170,
        "yellow_cards": 0,
        "red_cards": 0,
    }
    unknown = dict(row, transfermarkt_id=111)

    response = _client(competitions).post(
        "/ingestion/transfermarkt/competition-lines",
        json={
            "competition": "Champions League",
            "kind": "continental",
            "season_label": "2026",
            "rows": [row, unknown],
        },
    )

    assert response.json()["ingested"] == 1
    [line] = competitions.list_competition_lines(7)
    assert (line.competition, line.season_label, line.goals) == (
        "Champions League",
        "2026",
        1,
    )
