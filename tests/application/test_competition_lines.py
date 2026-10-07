from dataclasses import replace

from player_scouting.application.ports import DatasetCompetitionRow
from player_scouting.application.use_cases.competition_lines import (
    IngestDatasetCompetitionsUseCase,
    RecordCompetitionLinesUseCase,
)
from player_scouting.domain.competitions import CompetitionLine
from player_scouting.domain.entities import Player
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
CUP = replace(CHAMPIONS, competition="Copa del Rey", kind="cup", appearances=5)


def _repositories():
    players = InMemoryPlayerRepository()
    players.save_player(Player(7, "Lamine Yamal", "Forward", None, birth_year=2007))
    players.set_transfermarkt_id(7, 937958)
    return players, InMemoryCompetitionStatsRepository()


def test_lines_are_stored_for_the_players_we_know_by_transfermarkt_id():
    players, competitions = _repositories()
    rows = [
        DatasetCompetitionRow(937958, CHAMPIONS),
        DatasetCompetitionRow(937958, CUP),
        # Someone without a page here: nothing to show it on.
        DatasetCompetitionRow(111, CHAMPIONS),
    ]

    result = RecordCompetitionLinesUseCase(players, competitions).execute(rows)

    assert result.ingested == 2
    assert competitions.list_competition_lines(7) == [CHAMPIONS, CUP]


class FakeDataset:
    def __init__(self, rows):
        self.rows = rows
        self.since = None

    def competition_rows(self, since):
        self.since = since
        return self.rows


def test_the_dataset_brings_the_recent_seasons_of_every_competition():
    players, competitions = _repositories()
    dataset = FakeDataset([DatasetCompetitionRow(937958, CHAMPIONS)])

    result = IngestDatasetCompetitionsUseCase(dataset, players, competitions).execute(
        since=2019
    )

    assert dataset.since == 2019
    assert result.ingested == 1
