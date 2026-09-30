from datetime import date

import httpx

from player_scouting.application.ports import MatchRef
from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.mapper import to_match_ref, to_shot
from player_scouting.infrastructure.understat.shot_provider import UnderstatShotProvider

# Shapes captured from real calls to getLeagueData/La_liga/2026 and
# getMatchData/30770 during this session.
PLAYED_MATCH_RAW = {
    "id": "30770",
    "isResult": True,
    "h": {"id": "158", "title": "Alaves", "short_title": "ALA"},
    "a": {"id": "142", "title": "Getafe", "short_title": "GET"},
    "goals": {"h": "3", "a": "0"},
    "xG": {"h": "2.28581", "a": "0.259705"},
    "datetime": "2026-08-15 17:30:00",
}
UPCOMING_MATCH_RAW = dict(PLAYED_MATCH_RAW, id="30999", isResult=False)
SHOT_RAW = {
    "id": "688265",
    "minute": "10",
    "result": "BlockedShot",
    "X": "0.9080000305175782",
    "Y": "0.43",
    "xG": "0.029014641419053078",
    "player": "Nahuel Tenaglia",
    "h_a": "h",
    "player_id": "10364",
    "situation": "SetPiece",
    "season": "2026",
    "shotType": "Head",
    "match_id": "30770",
    "h_team": "Alaves",
    "a_team": "Getafe",
    "h_goals": "3",
    "a_goals": "0",
    "date": "2026-08-15 17:30:00",
    "player_assisted": "Denis Suárez",
    "lastAction": "Aerial",
}


def test_maps_a_played_match():
    match = to_match_ref(PLAYED_MATCH_RAW, competition="La Liga", season_label="2026")

    assert match == MatchRef(
        30770, "La Liga", "2026", date(2026, 8, 15), "Alaves", "Getafe"
    )


def test_maps_a_shot():
    shot = to_shot(SHOT_RAW)

    assert shot.shot_id == 688265
    assert shot.match_id == 30770
    assert shot.understat_player_id == 10364
    assert shot.player_name == "Nahuel Tenaglia"
    assert shot.minute == 10
    assert shot.result == "BlockedShot"
    assert (round(shot.x, 3), shot.y) == (0.908, 0.43)
    assert round(shot.xg, 4) == 0.029
    assert (shot.situation, shot.shot_type) == ("SetPiece", "Head")
    assert shot.home
    assert shot.assisted_by == "Denis Suárez"


def test_a_shot_without_assist_has_none():
    assert to_shot(dict(SHOT_RAW, player_assisted=None)).assisted_by is None


class FakeClient:
    def __init__(self) -> None:
        self.leagues: list[str] = []

    def get_league_matches(self, league: str, season: int) -> list[dict]:
        self.leagues.append(league)
        return [PLAYED_MATCH_RAW, UPCOMING_MATCH_RAW] if league == "La_liga" else []

    def get_match_shots(self, match_id: int) -> dict:
        return {"h": [SHOT_RAW], "a": []}


def test_provider_lists_only_played_matches_of_the_five_leagues():
    client = FakeClient()
    provider = UnderstatShotProvider(client, pause=lambda seconds: None)

    matches = provider.list_played_matches(2026)

    assert len(client.leagues) == 5
    assert [m.match_id for m in matches] == [30770]
    assert provider.get_match_shots(matches[0])[0].shot_id == 688265


def test_client_requests_match_data_with_ajax_headers():
    requested: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(
            200, json={"rosters": {}, "shots": {"h": [SHOT_RAW], "a": []}}
        )

    client = UnderstatClient(httpx.Client(transport=httpx.MockTransport(handler)))

    shots = client.get_match_shots(30770)

    assert shots["h"][0]["id"] == "688265"
    assert str(requested[0].url) == "https://understat.com/getMatchData/30770"
    assert requested[0].headers["X-Requested-With"] == "XMLHttpRequest"


def test_client_lists_league_matches():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"teams": {}, "players": [], "dates": [PLAYED_MATCH_RAW]}
        )

    client = UnderstatClient(httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.get_league_matches("La_liga", 2026) == [PLAYED_MATCH_RAW]


ROSTER_ROW = {
    "id": "794334",
    "goals": "1",
    "own_goals": "0",
    "shots": "3",
    "xG": "0.61",
    "time": "90",
    "player_id": "10364",
    "team_id": "158",
    "position": "FW",
    "player": "Nahuel Tenaglia",
    "h_a": "h",
    "yellow_card": "1",
    "red_card": "0",
    "roster_in": "0",
    "roster_out": "0",
    "key_passes": "2",
    "assists": "0",
    "xA": "0.12",
    "xGChain": "0.9",
    "xGBuildup": "0.1",
    "positionOrder": "15",
}


def test_maps_roster_lines_with_the_match_context():
    from player_scouting.infrastructure.understat.mapper import to_roster_entries

    match = to_match_ref(PLAYED_MATCH_RAW, competition="La Liga", season_label="2026")

    [entry] = to_roster_entries({"h": {"794334": ROSTER_ROW}, "a": {}}, match)

    assert (entry.team, entry.opponent, entry.home) == ("Alaves", "Getafe", True)
    assert (entry.understat_player_id, entry.player_name, entry.position) == (
        10364,
        "Nahuel Tenaglia",
        "FW",
    )
    assert (entry.minutes, entry.goals, entry.shots, entry.yellow) == (90, 1, 3, 1)
    assert (entry.xg, entry.xa, entry.key_passes) == (0.61, 0.12, 2)
