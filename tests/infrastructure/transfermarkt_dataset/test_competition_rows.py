# ruff: noqa: E501 - rows copied from the dataset, one per line.
import csv
import io
import zipfile

from player_scouting.domain.competitions import CompetitionLine
from player_scouting.infrastructure.transfermarkt_dataset.provider import (
    TransfermarktDatasetZipProvider,
)

# Real rows of Lamine Yamal in davidcariboo/player-scores (Oct 2026): a Champions
# League, a Copa del Rey, a Supercopa and a LaLiga game of 25/26, and a World Cup 2026
# game with Spain (clubs.csv has no national teams: the game names them).
GAMES = [
    {
        "game_id": "4715010",
        "competition_id": "CL",
        "season": "2025",
        "date": "2025-10-01",
        "home_club_id": "131",
        "away_club_id": "583",
        "home_club_name": "FC Barcelona",
        "away_club_name": "Paris Saint-Germain",
    },
    {
        "game_id": "4784340",
        "competition_id": "CDR",
        "season": "2025",
        "date": "2025-12-16",
        "home_club_id": "16576",
        "away_club_id": "131",
        "home_club_name": "CD Guadalajara",
        "away_club_name": "FC Barcelona",
    },
    {
        "game_id": "4790450",
        "competition_id": "SUC",
        "season": "2025",
        "date": "2026-01-07",
        "home_club_id": "131",
        "away_club_id": "621",
        "home_club_name": "FC Barcelona",
        "away_club_name": "Athletic Bilbao",
    },
    {
        "game_id": "4645608",
        "competition_id": "ES1",
        "season": "2025",
        "date": "2025-08-16",
        "home_club_id": "237",
        "away_club_id": "131",
        "home_club_name": "RCD Mallorca",
        "away_club_name": "FC Barcelona",
    },
    {
        "game_id": "4776613",
        "competition_id": "FIWC",
        "season": "2025",
        "date": "2026-06-15",
        "home_club_id": "3375",
        "away_club_id": "4311",
        "home_club_name": "Spain",
        "away_club_name": "Cape Verde",
    },
    # An older season and a Belgian play-off: neither is read.
    {
        "game_id": "1",
        "competition_id": "CL",
        "season": "2017",
        "date": "2017-10-01",
        "home_club_id": "131",
        "away_club_id": "583",
        "home_club_name": "FC Barcelona",
        "away_club_name": "Paris Saint-Germain",
    },
    {
        "game_id": "2",
        "competition_id": "EJPL",
        "season": "2025",
        "date": "2026-04-01",
        "home_club_id": "131",
        "away_club_id": "583",
        "home_club_name": "FC Barcelona",
        "away_club_name": "Paris Saint-Germain",
    },
]


def _appearance(game_id, competition, club, date, goals, assists, minutes, yellow=0):
    return {
        "appearance_id": f"{game_id}_937958",
        "game_id": game_id,
        "player_id": "937958",
        "player_club_id": club,
        "player_current_club_id": "131",
        "date": date,
        "player_name": "Lamine Yamal",
        "competition_id": competition,
        "yellow_cards": str(yellow),
        "red_cards": "0",
        "goals": str(goals),
        "assists": str(assists),
        "minutes_played": str(minutes),
    }


APPEARANCES = [
    _appearance("4715010", "CL", "131", "2025-10-01", 0, 0, 90, yellow=1),
    _appearance("4784340", "CDR", "131", "2025-12-16", 0, 1, 90),
    _appearance("4790450", "SUC", "131", "2026-01-07", 0, 0, 18),
    _appearance("4645608", "ES1", "131", "2025-08-16", 1, 1, 90),
    _appearance("4776613", "FIWC", "3375", "2026-06-15", 0, 0, 19),
    _appearance("1", "CL", "131", "2017-10-01", 3, 0, 90),
    _appearance("2", "EJPL", "131", "2026-04-01", 3, 0, 90),
]


def _csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


class FakeClient:
    def __init__(self, path) -> None:
        self._path = path

    def download_archive(self):
        return self._path


def _provider(tmp_path) -> TransfermarktDatasetZipProvider:
    path = tmp_path / "archive.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("games.csv", _csv(GAMES))
        archive.writestr("appearances.csv", _csv(APPEARANCES))
        archive.writestr(
            "clubs.csv", _csv([{"club_id": "131", "name": "FC Barcelona"}])
        )
    return TransfermarktDatasetZipProvider(FakeClient(path))


def test_every_competition_of_a_season_becomes_a_line(tmp_path):
    rows = _provider(tmp_path).competition_rows(since=2019)

    lines = {row.line.competition: row.line for row in rows}
    assert {row.transfermarkt_id for row in rows} == {937958}
    assert lines["Champions League"] == CompetitionLine(
        competition="Champions League",
        kind="continental",
        season_label="2025",
        team="FC Barcelona",
        appearances=1,
        goals=0,
        assists=0,
        minutes_played=90,
        yellow_cards=1,
        red_cards=0,
    )
    assert (lines["Copa del Rey"].kind, lines["Copa del Rey"].assists) == ("cup", 1)
    assert lines["Supercopa de España"].kind == "supercup"
    assert (lines["La Liga"].kind, lines["La Liga"].goals) == ("league", 1)


def test_a_national_team_line_is_labelled_with_the_tournament_year(tmp_path):
    rows = _provider(tmp_path).competition_rows(since=2019)

    [world_cup] = [r.line for r in rows if r.line.kind == "national"]

    assert (world_cup.competition, world_cup.season_label) == ("Mundial", "2026")
    assert world_cup.team == "Spain"


def test_older_seasons_and_unknown_competitions_are_left_out(tmp_path):
    rows = _provider(tmp_path).competition_rows(since=2019)

    assert len(rows) == 5
    assert all(row.line.season_label >= "2019" for row in rows)


def test_the_africa_cup_is_left_to_transfermarkt_pages(tmp_path):
    # The dataset files AFCON 2025 (played Dec 2025 - Jan 2026) under another season
    # than Transfermarkt's pages: read from one source only, it is not shown twice.
    from player_scouting.infrastructure.transfermarkt_dataset.mapper import (
        DATASET_COMPETITIONS,
    )

    assert "AFCN" not in DATASET_COMPETITIONS
