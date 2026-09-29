from __future__ import annotations

from datetime import date

import httpx

WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "player-scouting/0.1 (https://github.com/albertoqv/player-scouting)"

HUMAN_QID = "Q5"
ASSOCIATION_FOOTBALL_PLAYER_QID = "Q937857"
INSTANCE_OF_PROPERTY = "P31"
OCCUPATION_PROPERTY = "P106"
DATE_OF_BIRTH_PROPERTY = "P569"
COUNTRY_OF_CITIZENSHIP_PROPERTY = "P27"


class WikidataBirthDateProvider:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        api_url: str = WIKIDATA_API_URL,
    ) -> None:
        self._http_client = http_client or httpx.Client()
        self._api_url = api_url

    def find(self, name: str, nationality: str | None = None) -> date | None:
        candidate_ids = self._search_candidate_ids(name)
        if not candidate_ids:
            return None

        claims_by_id = self._fetch_claims(candidate_ids)
        footballers = [
            (entity_id, claims)
            for entity_id, claims in claims_by_id.items()
            if self._is_footballer(claims) and self._birth_date(claims) is not None
        ]

        if nationality is not None:
            footballers = self._filter_by_nationality(footballers, nationality)

        birth_dates = {self._birth_date(claims) for _, claims in footballers}
        if len(birth_dates) != 1:
            return None
        return next(iter(birth_dates))

    def _search_candidate_ids(self, name: str) -> list[str]:
        response = self._http_client.get(
            self._api_url,
            params={
                "action": "wbsearchentities",
                "search": name,
                "language": "en",
                "type": "item",
                "format": "json",
                "limit": 10,
            },
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return [result["id"] for result in response.json().get("search", [])]

    def _fetch_claims(self, entity_ids: list[str]) -> dict[str, dict]:
        response = self._http_client.get(
            self._api_url,
            params={
                "action": "wbgetentities",
                "ids": "|".join(entity_ids),
                "props": "claims",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        entities = response.json()["entities"]
        return {entity_id: entity["claims"] for entity_id, entity in entities.items()}

    def _filter_by_nationality(
        self, footballers: list[tuple[str, dict]], nationality: str
    ) -> list[tuple[str, dict]]:
        country_qids_by_entity = {
            entity_id: self._country_qid(claims) for entity_id, claims in footballers
        }
        country_qids = {
            qid for qid in country_qids_by_entity.values() if qid is not None
        }
        labels = self._fetch_labels(country_qids)
        return [
            (entity_id, claims)
            for entity_id, claims in footballers
            if labels.get(country_qids_by_entity[entity_id] or "", "").lower()
            == nationality.lower()
        ]

    def _fetch_labels(self, entity_ids: set[str]) -> dict[str, str]:
        if not entity_ids:
            return {}
        response = self._http_client.get(
            self._api_url,
            params={
                "action": "wbgetentities",
                "ids": "|".join(entity_ids),
                "props": "labels",
                "languages": "en",
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        entities = response.json()["entities"]
        return {
            entity_id: entity.get("labels", {}).get("en", {}).get("value", "")
            for entity_id, entity in entities.items()
        }

    @staticmethod
    def _is_footballer(claims: dict) -> bool:
        return WikidataBirthDateProvider._has_value(
            claims, INSTANCE_OF_PROPERTY, HUMAN_QID
        ) and WikidataBirthDateProvider._has_value(
            claims, OCCUPATION_PROPERTY, ASSOCIATION_FOOTBALL_PLAYER_QID
        )

    @staticmethod
    def _has_value(claims: dict, property_id: str, expected_qid: str) -> bool:
        for statement in claims.get(property_id, []):
            value = statement.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            if value.get("id") == expected_qid:
                return True
        return False

    @staticmethod
    def _birth_date(claims: dict) -> date | None:
        for statement in claims.get(DATE_OF_BIRTH_PROPERTY, []):
            time_value = (
                statement.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            ).get("time")
            if time_value:
                return date.fromisoformat(time_value.lstrip("+")[:10])
        return None

    @staticmethod
    def _country_qid(claims: dict) -> str | None:
        for statement in claims.get(COUNTRY_OF_CITIZENSHIP_PROPERTY, []):
            value = statement.get("mainsnak", {}).get("datavalue", {}).get("value", {})
            return value.get("id")
        return None
