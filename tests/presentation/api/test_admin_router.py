import json
from datetime import datetime

from fastapi.testclient import TestClient

from player_scouting.application.ports import HostingUsage
from player_scouting.infrastructure.persistence.overview import DataFreshness
from player_scouting.presentation.api.dependencies import (
    get_data_freshness,
    get_database_ping,
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
    app.dependency_overrides[get_data_freshness] = lambda: DataFreshness(
        missing_results=["Betis - Sevilla (La Liga, 2026-09-14)"],
        latest_result=datetime(2026, 9, 20),
        goal_mismatches=["Off (La Liga): FBref 5, Understat 2"],
    )
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


def _freshness_client(report):
    app = create_app()
    app.dependency_overrides[get_data_freshness] = lambda: report
    return TestClient(app)


def test_data_health_is_ok_when_every_played_match_has_its_result():
    report = DataFreshness(missing_results=[], latest_result=datetime(2026, 9, 20))

    response = _freshness_client(report).get("/health/data")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "missing_results": [],
        "goal_mismatches": [],
        "latest_result": "2026-09-20T00:00:00",
    }


def test_data_health_fails_loudly_when_results_stop_arriving():
    report = DataFreshness(
        missing_results=["Betis - Sevilla (La Liga, 2026-09-14)"],
        latest_result=datetime(2026, 9, 13),
    )

    response = _freshness_client(report).get("/health/data")

    assert response.status_code == 503
    assert response.json()["status"] == "stale"
    assert response.json()["missing_results"] == [
        "Betis - Sevilla (La Liga, 2026-09-14)"
    ]


def test_browser_errors_reach_the_panel_grouped_and_counted():
    client = _client(InMemoryVisitRepository())
    error = json.dumps({"message": "TypeError: x is undefined", "path": "/gemelos"})
    for _ in range(2):
        response = client.post(
            "/metrics/error",
            content=error,
            headers={"Content-Type": "text/plain", "User-Agent": CHROME},
        )
        assert response.status_code == 204

    body = client.get("/admin/dashboard", headers={"X-Ingestion-Key": "secret"}).json()

    [reported] = body["client_errors"]
    assert reported["message"] == "TypeError: x is undefined"
    assert reported["path"] == "/gemelos"
    assert reported["count"] == 2


def test_bots_and_garbage_are_not_browser_errors():
    client = _client(InMemoryVisitRepository())
    client.post(
        "/metrics/error",
        content=json.dumps({"message": "boom", "path": "/"}),
        headers={"User-Agent": "Googlebot/2.1"},
    )
    client.post("/metrics/error", content="not json", headers={"User-Agent": CHROME})

    body = client.get("/admin/dashboard", headers={"X-Ingestion-Key": "secret"}).json()

    assert body["client_errors"] == []


def test_the_panel_shows_the_data_quality_report():
    body = (
        _client(InMemoryVisitRepository())
        .get("/admin/dashboard", headers={"X-Ingestion-Key": "secret"})
        .json()
    )

    assert body["data_quality"]["missing_results"] == [
        "Betis - Sevilla (La Liga, 2026-09-14)"
    ]
    assert body["data_quality"]["goal_mismatches"] == [
        "Off (La Liga): FBref 5, Understat 2"
    ]


def test_the_database_round_trip_can_be_measured():
    app = create_app()
    app.dependency_overrides[get_database_ping] = lambda: lambda: None

    body = TestClient(app).get("/health/db").json()

    assert body["status"] == "ok"
    assert body["round_trip_ms"] >= 0
