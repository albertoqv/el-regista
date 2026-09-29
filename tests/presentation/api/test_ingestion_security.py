from fastapi.testclient import TestClient

from player_scouting.presentation.api.dependencies import (
    get_league_ingestion_job_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings
from tests.application.doubles import InMemoryLeagueIngestionJobRepository


def _client(ingestion_api_key: str) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_api_settings] = lambda: ApiSettings(
        ingestion_api_key=ingestion_api_key
    )
    app.dependency_overrides[get_league_ingestion_job_repository] = lambda: (
        InMemoryLeagueIngestionJobRepository()
    )
    return TestClient(app)


def test_allows_requests_when_no_key_is_configured():
    client = _client(ingestion_api_key="")

    response = client.get("/ingestion/leagues")

    assert response.status_code == 200


def test_rejects_requests_missing_the_header_when_a_key_is_configured():
    client = _client(ingestion_api_key="secret")

    response = client.get("/ingestion/leagues")

    assert response.status_code == 401


def test_rejects_requests_with_the_wrong_key():
    client = _client(ingestion_api_key="secret")

    response = client.get("/ingestion/leagues", headers={"X-Ingestion-Key": "wrong"})

    assert response.status_code == 401


def test_allows_requests_with_the_correct_key():
    client = _client(ingestion_api_key="secret")

    response = client.get("/ingestion/leagues", headers={"X-Ingestion-Key": "secret"})

    assert response.status_code == 200
