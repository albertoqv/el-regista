from datetime import date

from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.infrastructure.transfermarkt.mapper import (
    extract_date_of_birth,
    extract_photo_url,
    extract_preferred_foot,
    extract_profile_path,
    extract_search_candidates,
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


# Row structure verified against a real search for "Rodri" in this session:
# [name+links] [position] [club img] [age] [nationality img] [value] [agent]
SEARCH_WITH_AGES_HTML = """
<table class="items"><tbody>
  <tr class="odd">
    <td><table class="inline-table"><tr>
      <td><img title="Rodri" src="x.jpg"/></td>
      <td class="hauptlink"><a title="Rodri" href="/rodri/profil/spieler/357565">Rodri</a></td>
    </tr></table></td>
    <td class="zentriert">DM</td>
    <td class="zentriert"><img title="Manchester City" src="c.png"/></td>
    <td class="zentriert">30</td>
    <td class="zentriert"><img title="Spain" src="f.png"/></td>
    <td class="rechts hauptlink">€55.00m</td>
    <td class="rechts">Agent</td>
  </tr>
  <tr class="even">
    <td><table class="inline-table"><tr>
      <td class="hauptlink"><a title="Rodri" href="/rodri/profil/spieler/999999">Rodri</a></td>
    </tr></table></td>
    <td class="zentriert">CM</td>
    <td class="zentriert"><img title="Some Club" src="c.png"/></td>
    <td class="zentriert">19</td>
    <td class="zentriert"><img title="Spain" src="f.png"/></td>
    <td class="rechts hauptlink">€1.00m</td>
    <td class="rechts">-</td>
  </tr>
</tbody></table>
"""

PROFILE_HEADER_HTML = """
<div class="data-header__profile-container">
  <img src="https://img.a.transfermarkt.technology/portrait/header/581678-1748102891.jpg?lm=4711"
       class="data-header__profile-image" alt="Jude Bellingham"/>
</div>
<ul class="data-header__items">
  <li class="data-header__label">Date of birth/Age:
    <span itemprop="birthDate" class="data-header__content">29/06/2003 (23)</span>
  </li>
</ul>
"""


def test_extract_search_candidates_reads_path_name_club_and_age():
    candidates = extract_search_candidates(SEARCH_WITH_AGES_HTML)

    assert [(c.profile_path, c.name, c.club, c.age) for c in candidates] == [
        ("/rodri/profil/spieler/357565", "Rodri", "Manchester City", 30),
        ("/rodri/profil/spieler/999999", "Rodri", "Some Club", 19),
    ]


def test_extract_photo_url_reads_the_profile_header_image():
    assert extract_photo_url(PROFILE_HEADER_HTML) == (
        "https://img.a.transfermarkt.technology/portrait/header/581678-1748102891.jpg?lm=4711"
    )


def test_extract_date_of_birth_reads_the_birth_date_item():
    assert extract_date_of_birth(PROFILE_HEADER_HTML) == date(2003, 6, 29)


def test_profile_without_header_has_no_photo_or_birth_date():
    assert extract_photo_url("<div></div>") is None
    assert extract_date_of_birth("<div></div>") is None
