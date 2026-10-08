import json

from player_scouting.infrastructure.understat.history import (
    build_history,
    history_row,
)
from tests.infrastructure.understat.test_understat import YAMAL_RAW


def test_a_player_becomes_a_compact_row_with_his_position_group():
    row = history_row(dict(YAMAL_RAW, team_title="Barcelona,Getafe"))

    assert row == {
        "id": 11500,
        "name": "Lamine Yamal",
        "team": "Barcelona",
        "position": "Forward",
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
    index = json.loads((tmp_path / "index.json").read_text(encoding="utf-8"))
    assert index["Lionel Messi"] == [
        {"id": 2097, "competition": "La Liga", "year": 2017, "team": "Barcelona"}
    ]
    # A league season without players writes no file.
    assert not (tmp_path / "premier-league-2017.json").exists()
