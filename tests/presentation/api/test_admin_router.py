import json
from datetime import datetime

from fastapi.testclient import TestClient

from player_scouting.application.ports import HostingUsage
from player_scouting.presentation.api.dependencies import (
    get_database_overview,
    get_hosting_usage_provider,
    get_visit_repository,
)
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings
from tests.application.doubles import InMemoryVisitRepository

CHROME = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"


class FakeHosting:
    def current_usage(self):
        return HostingUsage(
            datetime(2026, 9, 29), datetime(2026, 10, 29), 0.14, 3.2, {"CPU": 0.01}, 5.0
        )


def _client(visits, key="secret", hosting=None):
    app = create_app()
    app.dependency_overrides[get_api_settings] = lambda: ApiSettings(
        ingestion_api_key=key, cors_origins="https://elregista.example"
    )
    app.dependency_overrides[get_visit_repository] = lambda: visits
    app.dependency_overrides[get_hosting_usage_provider] = lambda: hosting
    app.dependency_overrides[get_database_overview] = lambda: {"players": 9555}
    return TestClient(app)


def test_the_web_can_report_a_visit_as_plain_text_without_preflight():
    visits = InMemoryVisitRepository()

    response = _client(visits).post(
        "/metrics/visit",
        content=json.dumps({"path": "/gemelos", "referrer": "https://google.com/"}),
        headers={
            "Content-Type": "text/plain",
            "User-Agent": CHROME,
            "X-Forwarded-For": "81.0.0.1, 10.0.0.1",
        },
    )

    assert response.status_code == 204
    [view] = visits.views
    assert (view.path, view.referrer) == ("/gemelos", "google.com")


def test_a_malformed_visit_is_ignored_not_an_error():
    visits = InMemoryVisitRepository()

    response = _client(visits).post("/metrics/visit", content="not json")

    assert response.status_code == 204
    assert visits.views == []


def test_the_dashboard_needs_the_key():
    assert _client(InMemoryVisitRepository()).get("/admin/dashboard").status_code == 401


def test_the_dashboard_shows_visits_costs_data_and_api_health():
    visits = InMemoryVisitRepository()
    client = _client(visits, hosting=FakeHosting())
    client.post(
        "/metrics/visit",
        content=json.dumps({"path": "/"}),
        headers={"User-Agent": CHROME},
    )
    client.get("/health")

    body = client.get("/admin/dashboard", headers={"X-Ingestion-Key": "secret"}).json()

    assert body["views_today"] == 1
    assert len(body["daily"]) == 30
    assert body["top_pages"][0]["name"] == "/"
    assert body["hosting"]["current_dollars"] == 0.14
    assert body["hosting"]["line_items"] == {"CPU": 0.01}
    assert body["hosting_configured"] is True
    assert body["data"] == {"players": 9555}
    assert body["api"]["requests"] >= 2
    assert "p95_ms" in body["api"]


def test_without_a_railway_token_the_panel_says_so():
    body = (
        _client(InMemoryVisitRepository())
        .get("/admin/dashboard", headers={"X-Ingestion-Key": "secret"})
        .json()
    )

    assert body["hosting"] is None
    assert body["hosting_configured"] is False


def test_health_is_public():
    response = _client(InMemoryVisitRepository()).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
