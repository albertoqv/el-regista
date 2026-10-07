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


def test_a_player_in_two_clubs_of_one_competition_gets_one_line_added_up():
    # A mid-season move inside the league: both clubs' pages list him.
    players, competitions = _repositories()
    first = replace(
        CHAMPIONS, team="Villarreal", appearances=3, goals=1, minutes_played=200
    )
    second = replace(
        CHAMPIONS, team="FC Barcelona", appearances=4, goals=2, minutes_played=330
    )

    RecordCompetitionLinesUseCase(players, competitions).execute(
        [DatasetCompetitionRow(937958, first), DatasetCompetitionRow(937958, second)]
    )

    [line] = competitions.list_competition_lines(7)
    assert (line.appearances, line.goals, line.minutes_played) == (7, 3, 530)
    assert line.team == "FC Barcelona"


def _profile(tm_id: int, name: str):
    from datetime import date

    from player_scouting.application.ports import DatasetProfile
    from player_scouting.domain.market_value import MarketValuePoint

    return DatasetProfile(
        transfermarkt_id=tm_id,
        name=name,
        date_of_birth=date(1987, 6, 24),
        position="Forward",
        detailed_position="Right Winger",
        foot="left",
        height_cm=170,
        photo_url=f"https://img.a.transfermarkt.technology/portrait/header/{tm_id}.jpg",
        club="Inter Miami",
        valuations=(MarketValuePoint(date(2026, 6, 1), 15_000_000, "Inter Miami"),),
    )


class FakeDatasetWithProfiles(FakeDataset):
    def __init__(self, rows, profiles):
        super().__init__(rows)
        self._profiles = profiles

    def profiles(self):
        return self._profiles


def test_a_star_we_did_not_have_is_created_from_his_dataset_profile():
    # Messi left Europe before our league data starts: the dataset still has his
    # Barcelona, PSG and Champions League seasons.
    players, competitions = _repositories()
    messi_ligue = replace(CHAMPIONS, competition="Ligue 1", kind="league")
    unknown_eredivisie = replace(CHAMPIONS, competition="Eredivisie", kind="league")
    dataset = FakeDatasetWithProfiles(
        [
            DatasetCompetitionRow(28003, CHAMPIONS),
            DatasetCompetitionRow(28003, messi_ligue),
            DatasetCompetitionRow(555, unknown_eredivisie),
        ],
        [_profile(28003, "Lionel Messi"), _profile(555, "Someone")],
    )

    result = IngestDatasetCompetitionsUseCase(dataset, players, competitions).execute(
        since=2019
    )

    messi_id = players.transfermarkt_index()[28003]
    assert players.get_player(messi_id).name == "Lionel Messi"
    assert len(competitions.list_competition_lines(messi_id)) == 2
    assert players.list_market_value_history(messi_id)[0].amount_eur == 15_000_000
    # Only big-five and European football brings someone new; the rest waits.
    assert 555 not in players.transfermarkt_index()
    assert result.ingested == 2
