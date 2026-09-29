import httpx

from player_scouting.infrastructure.understat.client import UnderstatClient
from player_scouting.infrastructure.understat.mapper import to_advanced_row
from player_scouting.infrastructure.understat.provider import UnderstatSeasonProvider

# Shape captured from a real call to
# https://understat.com/getLeagueData/La_liga/2026 during this session.
YAMAL_RAW = {
    "id": "11500",
    "player_name": "Lamine Yamal",
    "games": "7",
    "time": "598",
    "goals": "7",
    "xG": "6.0812345",
    "assists": "4",
    "xA": "4.0798765",
    "shots": "28",
    "key_passes": "27",
    "yellow_cards": "1",
    "red_cards": "0",
    "position": "F M",
    "team_title": "Barcelona",
    "npg": "6",
    "npxG": "5.3",
    "xGChain": "9.51234",
    "xGBuildup": "2.0987",
}


def test_maps_a_real_shaped_row():
    row = to_advanced_row(YAMAL_RAW, competition="La Liga")

    assert row.competition == "La Liga"
    assert row.player.external_id == 11500
    assert row.player.name == "Lamine Yamal"
    assert row.player.teams == ("Barcelona",)
    assert (row.player.minutes, row.player.goals) == (598, 7)
    assert row.advanced.expected_goals == 6.08
    assert row.advanced.expected_assists == 4.08
    assert row.advanced.key_passes == 27
    assert row.advanced.xg_chain == 9.51
    assert row.advanced.xg_buildup == 2.1


def test_splits_the_teams_of_a_mid_season_transfer():
    raw = dict(YAMAL_RAW, team_title="Atletico Madrid,Deportivo La Coruna")

    row = to_advanced_row(raw, competition="La Liga")

    assert row.player.teams == ("Atletico Madrid", "Deportivo La Coruna")


def test_client_requests_league_data_with_ajax_headers():
    requested: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(200, json={"teams": {}, "players": [YAMAL_RAW]})

    client = UnderstatClient(httpx.Client(transport=httpx.MockTransport(handler)))

    players = client.get_league_players("La_liga", 2026)

    assert players == [YAMAL_RAW]
    assert str(requested[0].url) == "https://understat.com/getLeagueData/La_liga/2026"
    assert requested[0].headers["X-Requested-With"] == "XMLHttpRequest"


class FakeClient:
    def __init__(self) -> None:
        self.requested: list[tuple[str, int]] = []

    def get_league_players(self, league: str, season: int) -> list[dict]:
        self.requested.append((league, season))
        return [YAMAL_RAW] if league == "La_liga" else []


def test_provider_covers_the_five_big_leagues_with_our_competition_names():
    client = FakeClient()
    provider = UnderstatSeasonProvider(client, pause=lambda seconds: None)

    rows = provider.get_season(2026)

    assert [league for league, _ in client.requested] == [
        "EPL",
        "La_liga",
        "Bundesliga",
        "Serie_A",
        "Ligue_1",
    ]
    assert [row.competition for row in rows] == ["La Liga"]
