from fastapi.testclient import TestClient

from player_scouting.infrastructure.persistence.overview import DataFreshness
from player_scouting.presentation.api.dependencies import (
    get_data_freshness,
    get_database_overview,
    get_hosting_usage_provider,
    get_league_ingestion_job_repository,
    get_visit_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.security import admin_token
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings
from tests.application.doubles import (
    InMemoryLeagueIngestionJobRepository,
    InMemoryVisitRepository,
)


def _client(**settings) -> TestClient:
    values = ApiSettings(**settings)
    app = create_app(values)
    app.dependency_overrides[get_api_settings] = lambda: values
    app.dependency_overrides[get_league_ingestion_job_repository] = lambda: (
        InMemoryLeagueIngestionJobRepository()
    )
    app.dependency_overrides[get_visit_repository] = InMemoryVisitRepository
    app.dependency_overrides[get_hosting_usage_provider] = lambda: None
    app.dependency_overrides[get_database_overview] = lambda: {}
    app.dependency_overrides[get_data_freshness] = lambda: DataFreshness([], None)
    return TestClient(app)


def test_production_without_a_key_closes_ingestion_instead_of_opening_it():
    client = _client(ingestion_api_key="", require_ingestion_key=True)

    assert client.get("/ingestion/leagues").status_code == 503


def test_guessing_the_key_gets_an_address_blocked():
    client = _client(ingestion_api_key="secret")
    for attempt in range(10):
        wrong = {"X-Ingestion-Key": f"guess-{attempt}"}
        assert client.get("/ingestion/leagues", headers=wrong).status_code == 401

    right = {"X-Ingestion-Key": "secret"}
    assert client.get("/ingestion/leagues", headers=right).status_code == 429


def test_too_many_requests_from_one_address_are_refused():
    client = _client(rate_limit_per_minute=3)
    for _ in range(3):
        assert client.get("/health").status_code == 200

    response = client.get("/health")

    assert response.status_code == 429
    assert "retry-after" in response.headers


def test_the_api_map_is_hidden_in_production():
    client = _client(expose_docs=False)

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_the_admin_panel_works_with_a_short_lived_session_instead_of_the_key():
    client = _client(ingestion_api_key="secret")

    session = client.post("/admin/session", headers={"X-Ingestion-Key": "secret"})
    token = session.json()["token"]
    response = client.get(
        "/admin/dashboard", headers={"Authorization": f"Bearer {token}"}
    )

    assert session.status_code == 200
    assert "secret" not in token
    assert response.status_code == 200


def test_a_forged_or_expired_session_is_refused():
    client = _client(ingestion_api_key="secret")
    expired = admin_token("secret", expires_at=1)
    forged = admin_token("not-the-key", expires_at=4_102_444_800)

    for token in (expired, forged, "garbage"):
        response = client.get(
            "/admin/dashboard", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401


def test_on_vercel_the_api_is_closed_and_quiet_by_default(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    settings = ApiSettings()

    assert settings.require_ingestion_key is True
    assert settings.expose_docs is False


def test_locally_the_api_stays_open_for_development(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("REQUIRE_INGESTION_KEY", raising=False)
    monkeypatch.delenv("EXPOSE_DOCS", raising=False)

    settings = ApiSettings()

    assert settings.require_ingestion_key is False
    assert settings.expose_docs is True


def test_every_answer_carries_the_security_headers_zap_asked_for():
    # OWASP ZAP baseline (Oct 2026): 10021 and 90004 on every endpoint.
    client = TestClient(create_app(ApiSettings(_env_file=None)))

    for response in (client.get("/health"), client.get("/no-such-page")):
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"


def test_the_browser_beacons_stay_readable_from_the_web_origin():
    # The web posts visits and errors straight to the API (another site): same-origin
    # would make the browser block the answer and log an error on every page.
    client = TestClient(create_app(ApiSettings(_env_file=None)))

    response = client.post("/metrics/visit", content="not json")

    assert response.headers["Cross-Origin-Resource-Policy"] == "cross-origin"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
