import gzip

from fastapi.testclient import TestClient

from player_scouting.presentation.api.dependencies import get_backup_stream
from player_scouting.presentation.api.main import create_app
from player_scouting.presentation.api.settings import ApiSettings, get_api_settings


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_api_settings] = lambda: ApiSettings(
        ingestion_api_key="secret"
    )
    app.dependency_overrides[get_backup_stream] = lambda: (
        lambda: iter([b'COPY "players" ("player_id") FROM stdin;\n', b"1\n", b"\\.\n"])
    )
    return TestClient(app)


def test_the_backup_downloads_as_a_gzipped_sql_file():
    response = _client().get("/ingestion/backup", headers={"X-Ingestion-Key": "secret"})

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert ".sql.gz" in response.headers["content-disposition"]
    assert gzip.decompress(response.content) == (
        b'COPY "players" ("player_id") FROM stdin;\n1\n\\.\n'
    )


def test_the_backup_needs_the_ingestion_key():
    assert _client().get("/ingestion/backup").status_code == 401
