from datetime import date

from player_scouting.application.ports import (
    DatasetProfile,
    DatasetSeasonRow,
    ScrapedSeasonRow,
)
from player_scouting.application.use_cases.transfermarkt_dataset import (
    TRANSFERMARKT_ID_OFFSET,
    EnrichFromDatasetUseCase,
    IngestDatasetLeaguesUseCase,
    IngestScrapedLeagueSeasonUseCase,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.season import Season
from player_scouting.domain.statistics import Statistics
from tests.application.doubles import InMemoryPlayerRepository


def _profile(tm_id, name, born, **extra) -> DatasetProfile:
    values = dict(
        transfermarkt_id=tm_id,
        name=name,
        date_of_birth=born,
        position="Forward",
        detailed_position="Right Winger",
        foot="left",
        height_cm=183,
        photo_url=f"https://img.a.transfermarkt.technology/portrait/header/{tm_id}.jpg",
        club="FC Barcelona",
        valuations=(MarketValuePoint(date(2026, 6, 1), 200_000_000, "FC Barcelona"),),
    )
    values.update(extra)
    return DatasetProfile(**values)


class FakeDataset:
    def __init__(self, profiles, rows=()):
        self._profiles = profiles
        self._rows = rows

    def profiles(self):
        return list(self._profiles)

    def season_rows(self, start_year):
        return [row for row in self._rows if row.season_label == str(start_year)]


def test_enriches_matching_players_without_erasing_newer_data():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Lamine Yamal", "Forward", None, birth_year=2007))
    repository.save_player(
        Player(
            2,
            "Pedri",
            "Midfielder",
            None,
            birth_year=2002,
            photo_url="https://mine.jpg",
        )
    )
    repository.save_market_value_history(
        2, [MarketValuePoint(date(2026, 9, 1), 140_000_000, "FC Barcelona")]
    )
    dataset = FakeDataset(
        [
            _profile(937958, "Lamine Yamal", date(2007, 7, 13)),
            _profile(
                683840,
                "Pedri",
                date(2002, 11, 25),
                detailed_position="Central Midfield",
            ),
            _profile(1, "Lamine Yamal", date(1990, 1, 1)),  # homonym, wrong age
        ]
    )

    result = EnrichFromDatasetUseCase(dataset, repository).execute()

    assert result.ingested == 2
    yamal = repository.get_player(1)
    assert yamal.date_of_birth == date(2007, 7, 13)
    assert (yamal.height_cm, yamal.detailed_position) == (183, "Right Winger")
    assert yamal.photo_url.endswith("937958.jpg")
    assert repository.list_market_value_history(1)[0].amount_eur == 200_000_000
    pedri = repository.get_player(2)
    assert pedri.photo_url == "https://mine.jpg"
    # Our value is newer than the dataset's: kept.
    assert repository.list_market_value_history(2)[0].amount_eur == 140_000_000
    assert repository.transfermarkt_index() == {937958: 1, 683840: 2}


def test_adds_other_leagues_creating_players_or_reusing_known_ones():
    repository = InMemoryPlayerRepository()
    repository.save_player(
        Player(1, "Viktor Gyökeres", "Forward", None, birth_year=1998)
    )
    repository.set_transfermarkt_id(1, 325443)
    dataset = FakeDataset(
        [
            _profile(325443, "Viktor Gyökeres", date(1998, 6, 4)),
            _profile(900001, "Young Talent", date(2006, 3, 3), club="PSV Eindhoven"),
        ],
        rows=[
            DatasetSeasonRow(
                325443,
                "Liga Portugal",
                "2024",
                "Sporting CP",
                Statistics(39, 6, minutes_played=2900),
            ),
            DatasetSeasonRow(
                900001,
                "Eredivisie",
                "2025",
                "PSV Eindhoven",
                Statistics(8, 4, minutes_played=1500),
            ),
            DatasetSeasonRow(
                555, "Eredivisie", "2025", "Ajax", Statistics(1, 0)
            ),  # no profile
        ],
    )
    use_case = IngestDatasetLeaguesUseCase(dataset, repository)

    result = use_case.execute(2025)

    assert result.ingested == 1
    new_id = TRANSFERMARKT_ID_OFFSET + 900001
    talent = repository.get_player(new_id)
    assert talent.name == "Young Talent"
    assert talent.detailed_position == "Right Winger"
    assert (
        repository.get_season_statistics(new_id, Season("Eredivisie", "2025")).goals
        == 8
    )
    assert [s.player_id for s in result.skipped] == [555]

    use_case.execute(2024)
    assert (
        repository.get_season_statistics(1, Season("Liga Portugal", "2024")).goals == 39
    )


def test_falls_back_to_surname_and_birth_year_when_unique():
    repository = InMemoryPlayerRepository()
    repository.save_player(
        Player(1, "Dani Carvajal", "Defender", None, birth_year=1992)
    )
    dataset = FakeDataset([_profile(138927, "Daniel Carvajal", date(1992, 1, 11))])

    assert EnrichFromDatasetUseCase(dataset, repository).execute().ingested == 1
    assert repository.transfermarkt_index() == {138927: 1}


def test_two_dataset_players_claiming_the_same_player_are_both_ignored():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Rodri", "Midfielder", None, birth_year=1996))
    dataset = FakeDataset(
        [
            _profile(357565, "Rodri", date(1996, 6, 22)),
            _profile(400000, "Rodri", date(1996, 1, 1)),
        ]
    )

    assert EnrichFromDatasetUseCase(dataset, repository).execute().ingested == 0
    assert repository.get_player(1).photo_url is None


def _scraped(tm_id, name, team, goals, minutes=900):
    return ScrapedSeasonRow(
        transfermarkt_id=tm_id,
        name=name,
        position="Forward",
        detailed_position="Centre-Forward",
        team=team,
        statistics=Statistics(goals=goals, assists=1, minutes_played=minutes),
    )


def test_scraped_league_lines_land_on_players_we_already_know():
    repository = InMemoryPlayerRepository()
    repository.save_player(Player(1, "Ivan Perisic", "Forward", None))
    repository.set_transfermarkt_id(1, 42460)

    result = IngestScrapedLeagueSeasonUseCase(repository).execute(
        "Eredivisie", "2026", [_scraped(42460, "Ivan Perisic", "PSV Eindhoven", 2)]
    )

    assert result.ingested == 1
    season = Season("Eredivisie", "2026")
    assert repository.get_season_statistics(1, season).goals == 2
    assert repository.get_season_team(1, season) == "PSV Eindhoven"


def test_a_player_new_to_us_is_created_with_his_transfermarkt_id():
    repository = InMemoryPlayerRepository()

    IngestScrapedLeagueSeasonUseCase(repository).execute(
        "Eredivisie", "2026", [_scraped(215094, "Nick Olij", "PSV Eindhoven", 0)]
    )

    new_id = TRANSFERMARKT_ID_OFFSET + 215094
    created = repository.get_player(new_id)
    assert (created.name, created.detailed_position) == ("Nick Olij", "Centre-Forward")
    assert repository.transfermarkt_index()[215094] == new_id


def test_a_move_inside_the_league_adds_both_clubs_up():
    repository = InMemoryPlayerRepository()

    result = IngestScrapedLeagueSeasonUseCase(repository).execute(
        "Süper Lig",
        "2026",
        [
            _scraped(7, "Mover", "Galatasaray", 2, minutes=300),
            _scraped(7, "Mover", "Fenerbahce", 1, minutes=200),
        ],
    )

    assert result.ingested == 1
    season = Season("Süper Lig", "2026")
    player_id = TRANSFERMARKT_ID_OFFSET + 7
    stats = repository.get_season_statistics(player_id, season)
    assert (stats.goals, stats.assists, stats.minutes_played) == (3, 2, 500)
    assert repository.get_season_team(player_id, season) == "Galatasaray, Fenerbahce"
