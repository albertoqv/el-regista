import csv
import io
import zipfile
from datetime import date

from player_scouting.infrastructure.transfermarkt_dataset.mapper import to_profile
from player_scouting.infrastructure.transfermarkt_dataset.provider import (
    TransfermarktDatasetZipProvider,
)

# Row copied from players.csv of davidcariboo/player-scores (Sept 2026).
YAMAL_ROW = {
    "player_id": "937958",
    "name": "Lamine Yamal",
    "last_season": "2025",
    "date_of_birth": "2007-07-13 00:00:00",
    "sub_position": "Right Winger",
    "position": "Attack",
    "foot": "left",
    "height_in_cm": "183",
    "image_url": "https://img.a.transfermarkt.technology/portrait/header/937958-1773173768.jpg?lm=1",
    "current_club_name": "FC Barcelona",
    "market_value_in_eur": "200000000",
}


def test_maps_a_real_player_row():
    profile = to_profile(YAMAL_ROW, valuations=())

    assert profile.transfermarkt_id == 937958
    assert profile.name == "Lamine Yamal"
    assert profile.date_of_birth == date(2007, 7, 13)
    assert (profile.position, profile.detailed_position) == ("Forward", "Right Winger")
    assert (profile.foot, profile.height_cm) == ("left", 183)
    assert profile.photo_url.startswith("https://img.a.transfermarkt.technology/")
    assert profile.club == "FC Barcelona"


def test_missing_values_become_none_and_default_photos_are_ignored():
    row = dict(
        YAMAL_ROW,
        foot="",
        height_in_cm="",
        date_of_birth="",
        image_url="https://img.a.transfermarkt.technology/portrait/header/default.jpg?lm=1",
    )

    profile = to_profile(row, valuations=())

    assert (profile.foot, profile.height_cm, profile.date_of_birth) == (
        None,
        None,
        None,
    )
    assert profile.photo_url is None


def test_a_player_without_position_is_skipped():
    assert to_profile(dict(YAMAL_ROW, position="Missing"), valuations=()) is None


def _csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _archive(path) -> None:
    files = {
        "players.csv": [
            dict(YAMAL_ROW),
            dict(YAMAL_ROW, player_id="1", name="Old Retired", last_season="2010"),
        ],
        "player_valuations.csv": [
            {
                "player_id": "937958",
                "date": "2026-06-01",
                "market_value_in_eur": "200000000",
                "current_club_name": "FC Barcelona",
            },
            {
                "player_id": "937958",
                "date": "2024-01-01",
                "market_value_in_eur": "90000000",
                "current_club_name": "FC Barcelona",
            },
        ],
        "games.csv": [
            {"game_id": "10", "competition_id": "NL1", "season": "2025"},
            {"game_id": "11", "competition_id": "NL1", "season": "2025"},
            {"game_id": "12", "competition_id": "ES1", "season": "2025"},
            {"game_id": "13", "competition_id": "NL1", "season": "2024"},
        ],
        "clubs.csv": [{"club_id": "383", "name": "PSV Eindhoven"}],
        "appearances.csv": [
            {
                "game_id": "10",
                "player_id": "937958",
                "player_club_id": "383",
                "date": "2025-08-10",
                "competition_id": "NL1",
                "yellow_cards": "1",
                "red_cards": "0",
                "goals": "2",
                "assists": "0",
                "minutes_played": "90",
            },
            {
                "game_id": "11",
                "player_id": "937958",
                "player_club_id": "383",
                "date": "2025-08-17",
                "competition_id": "NL1",
                "yellow_cards": "0",
                "red_cards": "0",
                "goals": "1",
                "assists": "1",
                "minutes_played": "75",
            },
            {
                "game_id": "12",
                "player_id": "937958",
                "player_club_id": "131",
                "date": "2025-08-20",
                "competition_id": "ES1",
                "yellow_cards": "0",
                "red_cards": "0",
                "goals": "5",
                "assists": "0",
                "minutes_played": "90",
            },
            {
                "game_id": "13",
                "player_id": "937958",
                "player_club_id": "383",
                "date": "2024-08-10",
                "competition_id": "NL1",
                "yellow_cards": "0",
                "red_cards": "0",
                "goals": "9",
                "assists": "0",
                "minutes_played": "90",
            },
        ],
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, rows in files.items():
            archive.writestr(name, _csv(rows))


class FakeClient:
    def __init__(self, path) -> None:
        self._path = path
        self.downloads = 0

    def download_archive(self):
        self.downloads += 1
        return self._path


def test_provider_reads_recent_profiles_with_their_valuations(tmp_path):
    path = tmp_path / "archive.zip"
    _archive(path)
    client = FakeClient(path)
    provider = TransfermarktDatasetZipProvider(client, active_since=2023)

    [profile] = provider.profiles()

    assert profile.name == "Lamine Yamal"
    assert [v.amount_eur for v in profile.valuations] == [90_000_000, 200_000_000]
    assert profile.valuations[-1].club == "FC Barcelona"


def test_provider_sums_other_league_seasons_and_downloads_once(tmp_path):
    path = tmp_path / "archive.zip"
    _archive(path)
    client = FakeClient(path)
    provider = TransfermarktDatasetZipProvider(client, active_since=2023)

    [row] = provider.season_rows(2025)
    provider.profiles()

    assert (row.competition, row.season_label, row.team) == (
        "Eredivisie",
        "2025",
        "PSV Eindhoven",
    )
    assert (row.statistics.goals, row.statistics.assists) == (3, 1)
    assert (row.statistics.minutes_played, row.statistics.yellow_cards) == (165, 1)
    assert client.downloads == 1
