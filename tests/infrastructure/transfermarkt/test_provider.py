from datetime import date

import httpx
import pytest

from player_scouting.application.ports import EnrichmentUnavailableError
from player_scouting.infrastructure.transfermarkt.provider import (
    TransfermarktMarketValueProvider,
)


def _search_html(*rows: tuple[str, str, int]) -> str:
    """rows: (name, profile path, age) — cell layout verified against a real search."""
    body = "".join(
        f"""<tr class="odd">
          <td><table class="inline-table"><tr>
            <td class="hauptlink"><a title="{name}" href="{path}">{name}</a></td>
          </tr></table></td>
          <td class="zentriert">MF</td>
          <td class="zentriert"><img title="Some Club"/></td>
          <td class="zentriert">{age}</td>
        </tr>"""
        for name, path, age in rows
    )
    return f'<table class="items"><tbody>{body}</tbody></table>'


BELLINGHAM_SEARCH = _search_html(
    ("Jude Bellingham", "/jude-bellingham/profil/spieler/581678", 23)
)

PROFILE_HTML = """
<img src="https://img.a.transfermarkt.technology/portrait/header/581678.jpg"
     class="data-header__profile-image"/>
<span itemprop="birthDate">29/06/2003 (23)</span>
<span class="info-table__content info-table__content--regular">Foot:</span>
<span class="info-table__content info-table__content--bold">right</span>
"""

MARKET_VALUE_GRAPH_JSON = {
    "list": [
        {"y": 2500000, "datum_mw": "17/10/2019", "verein": "Birmingham City"},
        {"y": 160000000, "datum_mw": "01/01/2025", "verein": "Real Madrid"},
    ]
}


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://www.transfermarkt.com/x")
    return httpx.HTTPStatusError(
        "error", request=request, response=httpx.Response(status, request=request)
    )


class FakeTransfermarktClient:
    def __init__(
        self,
        search_html: str = BELLINGHAM_SEARCH,
        profile_error: int | None = None,
        search_error: int | None = None,
    ) -> None:
        self._search_html = search_html
        self._profile_error = profile_error
        self._search_error = search_error
        self.requested_profile_paths: list[str] = []
        self.requested_player_ids: list[int] = []

    def search_player(self, name: str) -> str:
        if self._search_error:
            raise _status_error(self._search_error)
        return self._search_html

    def get_profile(self, profile_path: str) -> str:
        if self._profile_error:
            raise _status_error(self._profile_error)
        self.requested_profile_paths.append(profile_path)
        return PROFILE_HTML

    def get_market_value_graph(self, player_id: int) -> dict:
        self.requested_player_ids.append(player_id)
        return MARKET_VALUE_GRAPH_JSON


def _provider(client: FakeTransfermarktClient) -> TransfermarktMarketValueProvider:
    return TransfermarktMarketValueProvider(client, current_year=lambda: 2026)


def test_builds_a_full_profile_for_a_found_player():
    client = FakeTransfermarktClient()

    result = _provider(client).get_market_value_history("Jude Bellingham", 2003)

    assert result is not None
    assert result.preferred_foot == "right"
    assert result.photo_url == (
        "https://img.a.transfermarkt.technology/portrait/header/581678.jpg"
    )
    assert result.date_of_birth == date(2003, 6, 29)
    assert result.points[-1].amount_eur == 160_000_000
    assert client.requested_player_ids == [581678]


def test_picks_the_homonym_whose_age_matches_the_birth_year():
    client = FakeTransfermarktClient(
        search_html=_search_html(
            ("Rodri", "/rodri/profil/spieler/999999", 19),
            ("Rodri", "/rodri/profil/spieler/357565", 30),
        )
    )

    _provider(client).get_market_value_history("Rodri", 1996)

    assert client.requested_profile_paths == ["/rodri/profil/spieler/357565"]


def test_does_not_guess_when_no_candidate_has_the_right_age():
    client = FakeTransfermarktClient(
        search_html=_search_html(("Rodri", "/rodri/profil/spieler/999999", 19))
    )

    assert _provider(client).get_market_value_history("Rodri", 1996) is None


def test_ignores_candidates_whose_name_does_not_share_any_word():
    client = FakeTransfermarktClient(
        search_html=_search_html(("Rodrygo", "/rodrygo/profil/spieler/412363", 30))
    )

    assert _provider(client).get_market_value_history("Rodri", 1996) is None


def test_without_birth_year_takes_the_first_matching_name():
    client = FakeTransfermarktClient()

    result = _provider(client).get_market_value_history("Jude Bellingham")

    assert result is not None


def test_returns_none_when_the_profile_is_not_found():
    client = FakeTransfermarktClient(profile_error=404)

    assert _provider(client).get_market_value_history("Jude Bellingham", 2003) is None


def test_raises_when_transfermarkt_is_blocking_us():
    client = FakeTransfermarktClient(search_error=429)

    with pytest.raises(EnrichmentUnavailableError):
        _provider(client).get_market_value_history("Jude Bellingham", 2003)
