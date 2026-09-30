from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from typing import Protocol

import httpx

from player_scouting.application.player_matching import name_tokens
from player_scouting.application.ports import (
    EnrichmentUnavailableError,
    MarketValueHistoryResult,
)
from player_scouting.infrastructure.transfermarkt.mapper import (
    SearchCandidate,
    extract_date_of_birth,
    extract_photo_url,
    extract_preferred_foot,
    extract_search_candidates,
    to_market_value_points,
)

PLAYER_ID_PATTERN = re.compile(r"/profil/spieler/(\d+)$")
NOT_FOUND = 404


class TransfermarktPages(Protocol):
    def search_player(self, name: str) -> str: ...

    def get_profile(self, profile_path: str) -> str: ...

    def get_market_value_graph(self, player_id: int) -> dict: ...


def _choose_candidate(
    candidates: list[SearchCandidate],
    player_name: str,
    birth_year: int | None,
    current_year: int,
) -> SearchCandidate | None:
    wanted = name_tokens(player_name)
    named = [c for c in candidates if name_tokens(c.name) & wanted]
    if birth_year is None:
        return named[0] if named else None
    expected_age = current_year - birth_year
    for candidate in named:
        # Birthdays later in the year make the age one less than the difference.
        if candidate.age in (expected_age, expected_age - 1):
            return candidate
    return None


class TransfermarktMarketValueProvider:
    def __init__(
        self,
        client: TransfermarktPages,
        current_year: Callable[[], int] = lambda: date.today().year,
    ) -> None:
        self._client = client
        self._current_year = current_year

    def get_market_value_history(
        self, player_name: str, birth_year: int | None = None
    ) -> MarketValueHistoryResult | None:
        try:
            return self._fetch(player_name, birth_year)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == NOT_FOUND:
                return None
            raise EnrichmentUnavailableError(str(error)) from error
        except httpx.TransportError as error:
            raise EnrichmentUnavailableError(str(error)) from error

    def _fetch(
        self, player_name: str, birth_year: int | None
    ) -> MarketValueHistoryResult | None:
        candidates = extract_search_candidates(self._client.search_player(player_name))
        candidate = _choose_candidate(
            candidates, player_name, birth_year, self._current_year()
        )
        if candidate is None:
            return None
        match = PLAYER_ID_PATTERN.search(candidate.profile_path)
        if match is None:
            return None

        profile_html = self._client.get_profile(candidate.profile_path)
        graph = self._client.get_market_value_graph(int(match.group(1)))
        return MarketValueHistoryResult(
            preferred_foot=extract_preferred_foot(profile_html),
            points=to_market_value_points(graph.get("list", [])),
            photo_url=extract_photo_url(profile_html),
            date_of_birth=extract_date_of_birth(profile_html),
        )
