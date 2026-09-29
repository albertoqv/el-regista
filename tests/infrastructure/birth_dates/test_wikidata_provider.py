from datetime import date

import httpx

from player_scouting.infrastructure.birth_dates.wikidata_provider import (
    WikidataBirthDateProvider,
)


def _binding(birth_date: str, country: str | None = None) -> dict:
    result = {"birthDate": {"value": birth_date}}
    if country is not None:
        result["countryLabel"] = {"value": country}
    return result


def _provider_with_bindings(bindings: list[dict]) -> WikidataBirthDateProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": {"bindings": bindings}})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return WikidataBirthDateProvider(http_client=http_client)


def test_returns_the_birth_date_for_a_single_unambiguous_match():
    provider = _provider_with_bindings(
        [_binding("1987-06-24T00:00:00Z", "Argentina")]
    )

    result = provider.find("Lionel Messi")

    assert result == date(1987, 6, 24)


def test_returns_none_when_there_are_no_matches():
    provider = _provider_with_bindings([])

    result = provider.find("Nobody Famous")

    assert result is None


def test_returns_none_when_multiple_people_share_the_same_name():
    provider = _provider_with_bindings(
        [
            _binding("1987-06-24T00:00:00Z", "Argentina"),
            _binding("1990-01-01T00:00:00Z", "Spain"),
        ]
    )

    result = provider.find("Common Name")

    assert result is None


def test_disambiguates_using_nationality_when_provided():
    provider = _provider_with_bindings(
        [
            _binding("1987-06-24T00:00:00Z", "Argentina"),
            _binding("1990-01-01T00:00:00Z", "Spain"),
        ]
    )

    result = provider.find("Common Name", nationality="Spain")

    assert result == date(1990, 1, 1)


def test_returns_none_when_nationality_does_not_match_any_candidate():
    provider = _provider_with_bindings([_binding("1987-06-24T00:00:00Z", "Argentina")])

    result = provider.find("Lionel Messi", nationality="Brazil")

    assert result is None
