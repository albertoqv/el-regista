# ruff: noqa: E501 - fixtures are real HTML, kept on one line as served.
import httpx
import pytest

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.client import TransfermarktClient
from player_scouting.infrastructure.transfermarkt.league_pages import (
    ClubLink,
    ScrapedLine,
    TransfermarktLeagueScraper,
    extract_club_season,
    extract_league_clubs,
)

# Shape captured from a real league page (Oct 2026),
# https://www.transfermarkt.com/eredivisie/startseite/wettbewerb/NL1
LEAGUE_HTML = """
<a href="/ado-den-haag/startseite/verein/1268/saison_id/2026">ADO (fuera de la tabla)</a>
<table class="items"><tbody>
<tr class="odd">
<td class="zentriert no-border-rechts"><a href="/psv-eindhoven/startseite/verein/383/saison_id/2026" title="PSV Eindhoven"><img alt="PSV Eindhoven" class="tiny_wappen" src="https://img.a.transfermarkt.technology/wappen/tiny/383.png" title="PSV Eindhoven"/></a></td><td class="hauptlink no-border-links"><a href="/psv-eindhoven/startseite/verein/383/saison_id/2026" title="PSV Eindhoven">PSV Eindhoven</a> <a href="#"><img alt="Dutch Champion 25/26" class="tabelle-erfolg" src="https://img.a.transfermarkt.technology/erfolge/mini/16.png" title="Dutch Champion 25/26"/></a></td><td class="zentriert"><a href="/psv-eindhoven/kader/verein/383/saison_id/2026" title="PSV Eindhoven">31</a></td><td class="zentriert">25.1</td>
</tr>
<tr class="even">
<td class="zentriert no-border-rechts"><a href="/ajax-amsterdam/startseite/verein/610/saison_id/2026" title="Ajax Amsterdam"><img alt="Ajax Amsterdam" class="tiny_wappen" src="https://img.a.transfermarkt.technology/wappen/tiny/610.png" title="Ajax Amsterdam"/></a></td><td class="hauptlink no-border-links"><a href="/ajax-amsterdam/startseite/verein/610/saison_id/2026" title="Ajax Amsterdam">Ajax Amsterdam</a></td><td class="zentriert"><a href="/ajax-amsterdam/kader/verein/610/saison_id/2026" title="Ajax Amsterdam">29</a></td><td class="zentriert">24.3</td>
</tr>
</tbody></table>
"""

# Shape captured from a real club page (Oct 2026),
# https://www.transfermarkt.com/psv-eindhoven/leistungsdaten/verein/383/reldata/NL1%262026/plus/1
# (Perisic's minutes written as later in the season, with a thousands separator).
CLUB_HTML = """
<table class="items"><tbody>
<tr class="even">
<td class="zentriert rueckennummer bg_Sturm" title="Attack"><div class="rn_nummer">5</div></td><td class="posrela" title=""><table class="inline-table" title=""><tr><td class="" rowspan="2"><a href="#"><img alt="Ivan Perisic" class="bilderrahmen-fixed" src="https://img.a.transfermarkt.technology/portrait/small/42460-1667991317.jpg" title="Ivan Perisic"/></a></td><td class="hauptlink"><div class="di nowrap"><span class="hide-for-small"><a href="/ivan-perisic/profil/spieler/42460" title="Ivan Perisic">Ivan Perisic</a></span></div><div class="di nowrap"><span class="show-for-small"><a href="/ivan-perisic/profil/spieler/42460" title="Ivan Perisic">I. Perisic</a></span></div></td></tr><tr><td>Right Winger</td></tr></table></td><td class="zentriert">37</td><td class="zentriert"><img alt="Croatia" class="flaggenrahmen" src="https://img.a.transfermarkt.technology/flagge/verysmall/37.png" title="Croatia"/></td><td class="zentriert">7</td><td class="zentriert" colspan="1">7</td><td class="zentriert">2</td><td class="zentriert">1</td><td class="zentriert">2</td><td class="zentriert">1</td><td class="zentriert">-</td><td class="zentriert">1</td><td class="zentriert">4</td><td class="zentriert cp" title="Points average of club: 2.29">2.29</td><td class="rechts">1.486'</td>
</tr>
<tr class="odd">
<td class="zentriert rueckennummer bg_Torwart" title="Goalkeeper"><div class="rn_nummer">16</div></td><td class="posrela" title=""><table class="inline-table" title=""><tr><td class="" rowspan="2"><a href="#"><img alt="Nick Olij" class="bilderrahmen-fixed" src="https://img.a.transfermarkt.technology/portrait/small/default.jpg" title="Nick Olij"/></a></td><td class="hauptlink"><div class="di nowrap"><span class="hide-for-small"><a href="/nick-olij/profil/spieler/215094" title="Nick Olij">Nick Olij</a></span></div></td></tr><tr><td>Goalkeeper</td></tr></table></td><td class="zentriert">31</td><td class="zentriert"><img alt="Netherlands" class="flaggenrahmen" src="https://img.a.transfermarkt.technology/flagge/verysmall/122.png" title="Netherlands"/></td><td class="zentriert">7</td><td class="zentriert" colspan="10">Not used during this season</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert hide">-</td><td class="zentriert cp hide" title="Points average of club: 2.29">0</td><td class="rechts hide">-</td>
</tr>
</tbody></table>
"""


def test_finds_the_clubs_of_the_league_table_only():
    assert extract_league_clubs(LEAGUE_HTML) == [
        ClubLink("PSV Eindhoven", "psv-eindhoven", 383),
        ClubLink("Ajax Amsterdam", "ajax-amsterdam", 610),
    ]


def test_reads_each_player_line_and_skips_those_who_did_not_play():
    [line] = extract_club_season(CLUB_HTML)

    assert line == ScrapedLine(
        transfermarkt_id=42460,
        name="Ivan Perisic",
        position="Forward",
        detailed_position="Right Winger",
        appearances=7,
        goals=2,
        assists=1,
        yellow_cards=2,
        # A second yellow is a sending off too.
        red_cards=1,
        minutes_played=1486,
    )


def _scraper(pages: dict[str, str], status: int = 200):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.raw_path.decode())
        page = pages.get(request.url.raw_path.decode())
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(200, text=page) if page else httpx.Response(404)

    client = TransfermarktClient(httpx.Client(transport=httpx.MockTransport(handler)))
    return TransfermarktLeagueScraper(client, pause_seconds=0), requested


def test_a_league_season_adds_up_every_club_page():
    scraper, requested = _scraper(
        {
            "/wettbewerb/startseite/wettbewerb/NL1/saison_id/2026": LEAGUE_HTML,
            "/psv-eindhoven/leistungsdaten/verein/383/reldata/NL1%262026/plus/1": CLUB_HTML,
            "/ajax-amsterdam/leistungsdaten/verein/610/reldata/NL1%262026/plus/1": "<table class='items'><tbody></tbody></table>",
        }
    )

    rows = scraper.league_season("NL1", 2026)

    assert len(requested) == 3
    [(team, line)] = rows
    assert team == "PSV Eindhoven"
    assert line.transfermarkt_id == 42460


def test_a_blocked_scraper_stops_instead_of_saving_half_a_league():
    scraper, _ = _scraper({}, status=403)

    with pytest.raises(EnrichmentUnavailableError):
        scraper.league_season("NL1", 2026)


def test_the_season_leagues_cover_second_divisions_with_verified_codes():
    from player_scouting.infrastructure.transfermarkt.league_pages import SEASON_LEAGUES

    # Codes read off Transfermarkt's country pages (Oct 2026).
    assert SEASON_LEAGUES["GB2"] == "Championship"
    assert SEASON_LEAGUES["ES2"] == "Segunda División"
    assert SEASON_LEAGUES["L2"] == "2. Bundesliga"
    assert len(SEASON_LEAGUES) == 28


def _flaky_scraper(failures_before_success: int):
    calls = {"n": 0}
    pages = {
        "/wettbewerb/startseite/wettbewerb/NL1/saison_id/2026": LEAGUE_HTML,
        "/psv-eindhoven/leistungsdaten/verein/383/reldata/NL1%262026/plus/1": CLUB_HTML,
        "/ajax-amsterdam/leistungsdaten/verein/610/reldata/NL1%262026/plus/1": "<table class='items'><tbody></tbody></table>",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.raw_path.decode()
        if "psv" in path and calls["n"] < failures_before_success:
            calls["n"] += 1
            raise httpx.ReadTimeout("slow page", request=request)
        return httpx.Response(200, text=pages[path])

    client = TransfermarktClient(httpx.Client(transport=httpx.MockTransport(handler)))
    return TransfermarktLeagueScraper(client, pause_seconds=0, retry_pause_seconds=0)


def test_a_page_that_times_out_once_is_tried_again():
    rows = _flaky_scraper(failures_before_success=1).league_season("NL1", 2026)

    assert [line.transfermarkt_id for _, line in rows] == [42460]


def test_a_page_that_never_answers_stops_the_run_instead_of_crashing_it():
    with pytest.raises(EnrichmentUnavailableError):
        _flaky_scraper(failures_before_success=99).league_season("NL1", 2026)
