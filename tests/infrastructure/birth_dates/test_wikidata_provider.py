from datetime import date

import httpx

from player_scouting.infrastructure.birth_dates.wikidata_provider import (
    WikidataBirthDateProvider,
)


def _search_result(qid: str) -> dict:
    return {"id": qid}


def _human_footballer_claims(birth_date: str, country_qid: str | None = None) -> dict:
    claims = {
        "P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}],
        "P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q937857"}}}}],
        "P569": [{"mainsnak": {"datavalue": {"value": {"time": birth_date}}}}],
    }
    if country_qid is not None:
        claims["P27"] = [{"mainsnak": {"datavalue": {"value": {"id": country_qid}}}}]
    return claims


def _non_footballer_claims() -> dict:
    return {
        "P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}],
        "P106": [{"mainsnak": {"datavalue": {"value": {"id": "Q82955"}}}}],
    }


def _provider_with(
    search_results: list[dict],
    claims_by_id: dict[str, dict],
    labels_by_id: dict[str, str] | None = None,
) -> WikidataBirthDateProvider:
    labels_by_id = labels_by_id or {}

    def handler(request: httpx.Request) -> httpx.Response:
        action = request.url.params.get("action")
        if action == "wbsearchentities":
            return httpx.Response(200, json={"search": search_results})
        if action == "wbgetentities":
            ids = request.url.params.get("ids").split("|")
            if request.url.params.get("props") == "labels":
                entities = {
                    qid: {"labels": {"en": {"value": labels_by_id[qid]}}}
                    for qid in ids
                    if qid in labels_by_id
                }
            else:
                entities = {qid: {"claims": claims_by_id[qid]} for qid in ids}
            return httpx.Response(200, json={"entities": entities})
        raise AssertionError(f"Unexpected action: {action}")

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return WikidataBirthDateProvider(http_client=http_client)


def test_returns_the_birth_date_for_a_single_unambiguous_match():
    provider = _provider_with(
        search_results=[_search_result("Q615")],
        claims_by_id={"Q615": _human_footballer_claims("+1987-06-24T00:00:00Z")},
    )

    result = provider.find("Lionel Messi")

    assert result == date(1987, 6, 24)


def test_returns_none_when_search_finds_no_candidates():
    provider = _provider_with(search_results=[], claims_by_id={})

    result = provider.find("Nobody Famous")

    assert result is None


def test_ignores_candidates_that_are_not_footballers():
    provider = _provider_with(
        search_results=[_search_result("Q1"), _search_result("Q2")],
        claims_by_id={
            "Q1": _non_footballer_claims(),
            "Q2": _human_footballer_claims("+1990-05-10T00:00:00Z"),
        },
    )

    result = provider.find("Some Name")

    assert result == date(1990, 5, 10)


def test_returns_none_when_multiple_footballer_candidates_have_different_birth_dates():
    provider = _provider_with(
        search_results=[_search_result("Q1"), _search_result("Q2")],
        claims_by_id={
            "Q1": _human_footballer_claims("+1987-06-24T00:00:00Z", "Q414"),
            "Q2": _human_footballer_claims("+1990-01-01T00:00:00Z", "Q29"),
        },
    )

    result = provider.find("Common Name")

    assert result is None


def test_disambiguates_using_nationality_when_provided():
    provider = _provider_with(
        search_results=[_search_result("Q1"), _search_result("Q2")],
        claims_by_id={
            "Q1": _human_footballer_claims("+1987-06-24T00:00:00Z", "Q414"),
            "Q2": _human_footballer_claims("+1990-01-01T00:00:00Z", "Q29"),
        },
        labels_by_id={"Q414": "Argentina", "Q29": "Spain"},
    )

    result = provider.find("Common Name", nationality="Spain")

    assert result == date(1990, 1, 1)


def test_returns_none_when_nationality_does_not_match_any_candidate():
    provider = _provider_with(
        search_results=[_search_result("Q1")],
        claims_by_id={"Q1": _human_footballer_claims("+1987-06-24T00:00:00Z", "Q414")},
        labels_by_id={"Q414": "Argentina"},
    )

    result = provider.find("Lionel Messi", nationality="Brazil")

    assert result is None


def test_sends_a_descriptive_user_agent():
    captured_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"search": []})

    provider = WikidataBirthDateProvider(
        http_client=httpx.Client(transport=httpx.MockTransport(handler))
    )

    provider.find("Someone")

    user_agent = captured_requests[0].headers.get("user-agent", "")
    assert "player-scouting" in user_agent.lower()
