from __future__ import annotations

from datetime import date

import httpx

DEFAULT_ENDPOINT = "https://query.wikidata.org/sparql"


def _escape_sparql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_query(name: str) -> str:
    escaped_name = _escape_sparql_string(name)
    return f"""
    SELECT ?birthDate ?countryLabel WHERE {{
      ?person rdfs:label ?label.
      FILTER(LCASE(STR(?label)) = LCASE("{escaped_name}"))
      ?person wdt:P31 wd:Q5.
      ?person wdt:P106 wd:Q937857.
      ?person wdt:P569 ?birthDate.
      OPTIONAL {{
        ?person wdt:P27 ?country.
        ?country rdfs:label ?countryLabel.
        FILTER(LANG(?countryLabel) = "en")
      }}
    }}
    """


class WikidataBirthDateProvider:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        endpoint: str = DEFAULT_ENDPOINT,
    ) -> None:
        self._http_client = http_client or httpx.Client()
        self._endpoint = endpoint

    def find(self, name: str, nationality: str | None = None) -> date | None:
        response = self._http_client.get(
            self._endpoint,
            params={"query": _build_query(name), "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
        )
        response.raise_for_status()
        bindings = response.json()["results"]["bindings"]

        candidates = [
            (
                binding["birthDate"]["value"],
                binding.get("countryLabel", {}).get("value"),
            )
            for binding in bindings
        ]

        if nationality is not None:
            candidates = [
                (birth_date, country)
                for birth_date, country in candidates
                if country is not None and country.lower() == nationality.lower()
            ]

        unique_dates = {birth_date for birth_date, _ in candidates}
        if len(unique_dates) != 1:
            return None

        return date.fromisoformat(next(iter(unique_dates))[:10])
