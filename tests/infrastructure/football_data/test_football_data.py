from datetime import date

import httpx

from player_scouting.infrastructure.football_data.client import FootballDataClient
from player_scouting.infrastructure.football_data.mapper import to_match_stats
from player_scouting.infrastructure.football_data.provider import FootballDataProvider

# Header and first row copied from football-data.co.uk/mmz4281/2627/SP1.csv
# (Sept 2026), trimmed to the columns we read plus a few odds.
PLAYED_CSV = (
    "﻿Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HTR,HxG,AxG,"
    "HS,AS,HST,AST,HF,AF,HC,AC,HY,AY,HR,AR,AvgH,AvgD,AvgA,Avg>2.5,Avg<2.5,"
    "AvgCH,AvgCD,AvgCA,AvgC>2.5,AvgC<2.5\n"
    "SP1,15/08/2026,18:30,Alaves,Getafe,3,0,H,0,0,D,1.93,0.24,18,6,8,2,16,13,5,3,"
    "4,3,0,1,2.33,2.82,3.62,3.08,1.35,2.32,2.76,3.75,3.32,1.32\n"
)
# From football-data.co.uk/fixtures.csv: upcoming match with referee, no stats.
UPCOMING_CSV = (
    "﻿Div,Date,Time,HomeTeam,AwayTeam,Referee,AvgH,AvgD,AvgA,Avg>2.5,Avg<2.5\n"
    "E0,10/10/2026,12:30,Arsenal,Leeds,M Oliver,1.4,4.8,7.5,1.6,2.3\n"
    "EC,29/09/2026,19:00,Boreham Wood,Kidderminster,A Humphries,1.33,5,7.5,1.5,2.5\n"
)


def _rows(text):
    import csv
    import io

    return list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))


def test_maps_a_played_match_with_every_stat_and_closing_odds():
    [row] = _rows(PLAYED_CSV)

    match = to_match_stats(row, competition="La Liga", season_label="2026")

    assert (match.home_team, match.away_team, match.played_on) == (
        "Alaves",
        "Getafe",
        date(2026, 8, 15),
    )
    assert (match.home_goals, match.away_goals) == (3, 0)
    assert (match.home_goals_ht, match.away_goals_ht) == (0, 0)
    assert (match.home_shots, match.away_shots) == (18, 6)
    assert (match.home_shots_on_target, match.away_shots_on_target) == (8, 2)
    assert (match.home_fouls, match.away_fouls) == (16, 13)
    assert (match.home_corners, match.away_corners) == (5, 3)
    assert (match.home_yellows, match.away_yellows) == (4, 3)
    assert (match.home_reds, match.away_reds) == (0, 1)
    # Closing odds are preferred: they know the most.
    assert (match.odds_home, match.odds_draw, match.odds_away) == (2.32, 2.76, 3.75)
    assert (match.odds_over_2_5, match.odds_under_2_5) == (3.32, 1.32)
    assert match.played


def test_maps_an_upcoming_match_with_its_referee():
    arsenal, _ = _rows(UPCOMING_CSV)

    match = to_match_stats(arsenal, competition="Premier League", season_label="2026")

    assert not match.played
    assert match.referee == "M Oliver"
    assert match.home_corners is None
    assert (match.odds_home, match.odds_draw, match.odds_away) == (1.4, 4.8, 7.5)


class FakeClient:
    def __init__(self):
        self.requested = []

    def season_csv(self, league_code, start_year):
        self.requested.append((league_code, start_year))
        return PLAYED_CSV if league_code == "SP1" else ""

    def upcoming_csv(self):
        return UPCOMING_CSV


def test_provider_reads_known_leagues_and_skips_the_rest():
    client = FakeClient()
    provider = FootballDataProvider(client, pause=lambda s: None)

    played = provider.season(2026)
    upcoming = provider.upcoming()

    assert ("SP1", 2026) in client.requested and ("E0", 2026) in client.requested
    assert [m.home_team for m in played] == ["Alaves"]
    assert [m.competition for m in upcoming] == ["Premier League"]  # "EC" is unknown


def test_client_builds_the_season_url_and_follows_the_redirect():
    requested = []

    def handler(request):
        requested.append(str(request.url))
        if request.url.host == "www.football-data.co.uk":
            return httpx.Response(
                302,
                headers={
                    "Location": "https://football-data.co.uk/mmz4281/2627/SP1.csv"
                },
            )
        return httpx.Response(200, text=PLAYED_CSV)

    client = FootballDataClient(httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.season_csv("SP1", 2026).startswith("﻿Div")
    assert requested[0] == "https://www.football-data.co.uk/mmz4281/2627/SP1.csv"
