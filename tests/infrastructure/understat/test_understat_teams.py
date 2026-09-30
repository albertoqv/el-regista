from datetime import datetime

from player_scouting.infrastructure.understat.mapper import to_fixture, to_team_matches

# Shapes captured from getLeagueData/La_liga/2026 during this session.
PLAYED = {
    "id": "30770",
    "isResult": True,
    "h": {"id": "158", "title": "Alaves", "short_title": "ALA"},
    "a": {"id": "142", "title": "Getafe", "short_title": "GET"},
    "goals": {"h": "3", "a": "0"},
    "xG": {"h": "2.28581", "a": "0.259705"},
    "datetime": "2026-08-15 17:30:00",
}
UPCOMING = {
    "id": "30840",
    "isResult": False,
    "h": {"id": "158", "title": "Alaves", "short_title": "ALA"},
    "a": {"id": "143", "title": "Atletico Madrid", "short_title": "ATL"},
    "goals": {"h": None, "a": None},
    "xG": {"h": None, "a": None},
    "datetime": "2026-10-11 15:00:00",
}
ALAVES_HISTORY_ROW = {
    "h_a": "h",
    "xG": 2.28581,
    "xGA": 0.259705,
    "npxG": 2.28581,
    "npxGA": 0.259705,
    "ppda": {"att": 274, "def": 19},
    "ppda_allowed": {"att": 249, "def": 33},
    "deep": 9,
    "deep_allowed": 2,
    "scored": 3,
    "missed": 0,
    "xpts": 2.6,
    "result": "w",
    "date": "2026-08-15 17:30:00",
    "wins": 1,
    "draws": 0,
    "loses": 0,
    "pts": 3,
    "npxGD": 2.02,
}


def test_maps_played_and_upcoming_fixtures():
    played = to_fixture(PLAYED, "La Liga", "2026")
    upcoming = to_fixture(UPCOMING, "La Liga", "2026")

    assert played.match_id == 30770
    assert (played.home_team, played.away_team) == ("Alaves", "Getafe")
    assert played.kickoff == datetime(2026, 8, 15, 17, 30)
    assert (played.home_goals, played.away_goals) == (3, 0)
    assert round(played.home_xg, 2) == 2.29
    assert upcoming.home_goals is None and not upcoming.played


def test_maps_team_history_rows_onto_their_matches():
    league_data = {
        "teams": {
            "158": {"id": "158", "title": "Alaves", "history": [ALAVES_HISTORY_ROW]}
        },
        "dates": [PLAYED, UPCOMING],
    }

    [match] = to_team_matches(league_data, "La Liga", "2026")

    assert (match.match_id, match.team, match.opponent, match.home) == (
        30770,
        "Alaves",
        "Getafe",
        True,
    )
    assert (match.goals_for, match.goals_against) == (3, 0)
    assert round(match.xg_for, 2) == 2.29
    assert match.ppda == 274 / 19
    assert match.ppda_allowed == 249 / 33
    assert (match.deep, match.deep_allowed) == (9, 2)
    assert match.xpts == 2.6


def test_team_provider_reads_the_five_leagues():
    from player_scouting.infrastructure.understat.team_provider import (
        UnderstatTeamProvider,
    )

    class Client:
        def __init__(self):
            self.leagues = []

        def get_league_data(self, league, season):
            self.leagues.append(league)
            if league != "La_liga":
                return {"teams": {}, "dates": []}
            return {
                "teams": {
                    "158": {
                        "id": "158",
                        "title": "Alaves",
                        "history": [ALAVES_HISTORY_ROW],
                    }
                },
                "dates": [PLAYED, UPCOMING],
            }

    client = Client()
    fixtures, matches = UnderstatTeamProvider(
        client, pause=lambda s: None
    ).get_team_season(2026)

    assert len(client.leagues) == 5
    assert [f.match_id for f in fixtures] == [30770, 30840]
    assert [m.team for m in matches] == ["Alaves"]
