from datetime import date

from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.infrastructure.transfermarkt.mapper import (
    extract_preferred_foot,
    extract_profile_path,
    to_market_value_points,
)

# Shape captured from a real search for "Jude Bellingham" on
# https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche during this session.
SEARCH_RESULTS_HTML = """
<table class="items">
  <tbody>
    <tr>
      <td class="hauptlink">
        <a href="/jude-bellingham/profil/spieler/581678" class="spielprofil_tooltip">
          Jude Bellingham
        </a>
      </td>
    </tr>
  </tbody>
</table>
"""

# Shape captured from a real profile page,
# https://www.transfermarkt.com/jude-bellingham/profil/spieler/581678
PROFILE_HTML = """
<div class="info-table">
  <span class="info-table__content info-table__content--regular">Foot:</span>
  <span class="info-table__content info-table__content--bold">right</span>
</div>
"""

# Shape captured from a real call to
# https://www.transfermarkt.com/ceapi/marketValueDevelopment/graph/581678
MARKET_VALUE_GRAPH_JSON = {
    "list": [
        {
            "x": 1571270400000,
            "y": 2500000,
            "datum_mw": "17/10/2019",
            "verein": "Birmingham City",
            "age": "16",
        },
        {
            "x": 1735689600000,
            "y": 160000000,
            "datum_mw": "01/01/2025",
            "verein": "Real Madrid",
            "age": "21",
        },
    ]
}


def test_extract_profile_path_finds_the_first_player_profile_link():
    path = extract_profile_path(SEARCH_RESULTS_HTML)

    assert path == "/jude-bellingham/profil/spieler/581678"


def test_extract_profile_path_returns_none_when_there_are_no_results():
    assert extract_profile_path("<html><body>no results</body></html>") is None


def test_extract_preferred_foot_reads_the_info_table():
    assert extract_preferred_foot(PROFILE_HTML) == "right"


def test_extract_preferred_foot_returns_none_when_missing():
    assert extract_preferred_foot("<div class='info-table'></div>") is None


def test_to_market_value_points_maps_and_sorts_by_date():
    points = to_market_value_points(MARKET_VALUE_GRAPH_JSON["list"])

    assert points == [
        MarketValuePoint(date(2019, 10, 17), 2_500_000, "Birmingham City"),
        MarketValuePoint(date(2025, 1, 1), 160_000_000, "Real Madrid"),
    ]
