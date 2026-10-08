import json

from player_scouting.infrastructure.understat.history import (
    build_history,
    build_profiles,
    history_row,
    index_key,
    write_index,
    write_profiles,
)
from tests.infrastructure.understat.test_understat import YAMAL_RAW


def test_a_player_becomes_a_compact_row_with_his_position_group():
    row = history_row(dict(YAMAL_RAW, team_title="Barcelona,Getafe"))

    assert row == {
        "id": 11500,
        "name": "Lamine Yamal",
        "team": "Barcelona",
        "position": "Forward",
        "games": 7,
        "minutes": 598,
        "goals": 7,
        "expected_goals": 6.08,
        "shots": 28,
        "assists": 4,
        "expected_assists": 4.08,
        "key_passes": 27,
        "xg_chain": 9.51,
        "xg_buildup": 2.1,
        "yellow_cards": 1,
        "red_cards": 0,
    }


class FakeUnderstat:
    def __init__(self):
        self.asked = []

    def get_league_players(self, league, season):
        self.asked.append((league, season))
        if (league, season) == ("La_liga", 2017):
            return [
                dict(YAMAL_RAW, id="2097", player_name="Lionel Messi", position="F")
            ]
        return []


def test_one_file_per_league_season_and_an_index_of_each_players_seasons(tmp_path):
    understat = FakeUnderstat()

    build_history(understat, ["La_liga", "EPL"], [2017], tmp_path, pause_seconds=0)

    assert understat.asked == [("La_liga", 2017), ("EPL", 2017)]
    season = json.loads((tmp_path / "la-liga-2017.json").read_text(encoding="utf-8"))
    assert season["competition"] == "La Liga"
    assert [p["name"] for p in season["players"]] == ["Lionel Messi"]
    index = json.loads((tmp_path / "index" / "l.json").read_text(encoding="utf-8"))
    assert index["lionel messi"] == [
        {
            "id": 2097,
            "name": "Lionel Messi",
            "competition": "La Liga",
            "year": 2017,
            "team": "Barcelona",
        }
    ]
    # A league season without players writes no file.
    assert not (tmp_path / "premier-league-2017.json").exists()


def test_the_index_is_split_by_initial_so_a_lookup_reads_a_small_file(tmp_path):
    understat = FakeUnderstat()
    build_history(understat, ["La_liga"], [2017], tmp_path, pause_seconds=0)
    for shard in (tmp_path / "index").iterdir():
        shard.unlink()

    write_index(tmp_path)

    shard = json.loads((tmp_path / "index" / "l.json").read_text(encoding="utf-8"))
    assert shard["lionel messi"][0]["year"] == 2017
    assert index_key("Ángel Di María") == "a"
    assert index_key("Özil") == "o"


def _row(id_, name, position="Forward", minutes=1800, **numbers):
    base = {
        "id": id_,
        "name": name,
        "team": "Barcelona",
        "position": position,
        "games": 20,
        "minutes": minutes,
        "goals": 0,
        "expected_goals": 0.0,
        "shots": 0,
        "assists": 0,
        "expected_assists": 0.0,
        "key_passes": 0,
        "xg_chain": 0.0,
        "xg_buildup": 0.0,
        "yellow_cards": 0,
        "red_cards": 0,
    }
    return base | numbers


def test_profiles_hold_each_regulars_percentiles_within_his_league_season_and_line():
    season = {
        "competition": "La Liga",
        "year": 2015,
        "players": [
            _row(1, "Messi", goals=26, expected_goals=20.0),
            _row(2, "Neymar", goals=24, expected_goals=18.0),
            # Twice the minutes for the same goals: half the rate.
            _row(3, "Suárez", minutes=3600, goals=26),
            _row(4, "Sub", minutes=400, goals=9),
            _row(5, "Busquets", position="Midfielder", goals=1),
            _row(6, "Bravo", position="Goalkeeper"),
        ],
    }

    profiles = build_profiles([season])

    # Goalkeepers are left out: Understat's metrics say nothing about them.
    assert set(profiles) == {"Forward", "Midfielder"}
    forwards = profiles["Forward"]
    assert forwards["competitions"] == ["La Liga"]
    rows = [dict(zip(forwards["fields"], row, strict=True)) for row in forwards["rows"]]
    # Below 900 minutes he is not a regular: neither listed nor a peer.
    assert [row["name"] for row in rows] == ["Messi", "Neymar", "Suárez"]
    messi = rows[0]
    assert messi["competition"] == 0
    assert messi["year"] == 2015
    assert messi["minutes"] == 1800
    assert messi["goals"] == 26
    assert messi["p_goals"] == 100
    # Neymar's 24 in 1800' beats only Suárez's 26 in 3600': 2 of 3 at or below.
    assert rows[1]["p_goals"] == 67
    assert rows[2]["p_goals"] == 33
    midfielder = dict(
        zip(
            profiles["Midfielder"]["fields"],
            profiles["Midfielder"]["rows"][0],
            strict=True,
        )
    )
    assert midfielder["p_goals"] == 100


def test_profiles_are_written_from_the_season_files(tmp_path):
    understat = FakeUnderstat()
    build_history(understat, ["La_liga"], [2017], tmp_path, pause_seconds=0)
    (tmp_path / "la-liga-2017.json").write_text(
        json.dumps(
            {"competition": "La Liga", "year": 2017, "players": [_row(2097, "Messi")]}
        ),
        encoding="utf-8",
    )

    write_profiles(tmp_path)

    forwards = json.loads(
        (tmp_path / "profiles" / "forward.json").read_text(encoding="utf-8")
    )
    assert forwards["rows"][0][forwards["fields"].index("id")] == 2097


def test_only_the_missing_seasons_are_read_again(tmp_path):
    (tmp_path / "la-liga-2017.json").write_text(
        json.dumps(
            {"competition": "La Liga", "year": 2017, "players": [_row(2097, "Messi")]}
        ),
        encoding="utf-8",
    )
    understat = FakeUnderstat()

    build_history(
        understat,
        ["La_liga", "EPL"],
        [2017],
        tmp_path,
        pause_seconds=0,
        missing_only=True,
    )

    assert understat.asked == [("EPL", 2017)]
    assert (tmp_path / "profiles" / "forward.json").exists()


def test_names_and_teams_come_without_html_entities():
    row = history_row(
        dict(
            YAMAL_RAW, player_name="N&#039;Golo Kanté", team_title="Brighton &amp; Hove"
        )
    )

    assert row["name"] == "N'Golo Kanté"
    assert row["team"] == "Brighton & Hove"
