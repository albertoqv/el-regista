import httpx
import pytest

from player_scouting.infrastructure.persistence.settings import Settings
from player_scouting.infrastructure.secrets import vault
from player_scouting.infrastructure.secrets.vault import (
    VaultUnavailableError,
    read_vault_secrets,
)
from player_scouting.presentation.api.settings import ApiSettings

# Real answers of a `vault server -dev` 2.1.1 (KV v2 mounted at secret/), Oct 2026.
SECRET_RESPONSE = (
    '{"request_id":"52352040-f67b-d9cf-4dfd-9de00812e825","lease_id":"",'
    '"renewable":false,"lease_duration":0,"data":{"data":{"database_url":'
    '"postgresql+psycopg://scouting:scouting@localhost:5433/scouting",'
    '"ingestion_api_key":"local-ingestion-key"},"metadata":{"created_time":'
    '"2026-10-05T15:33:08.386421Z","custom_metadata":null,"deletion_time":"",'
    '"destroyed":false,"version":1}},"wrap_info":null,"warnings":null,"auth":null,'
    '"mount_type":"kv"}'
)
MISSING_RESPONSE = '{"errors":[]}'


def _client(status: int, body: str, seen: list[httpx.Request]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(status, text=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_reads_the_secrets_of_a_kv_v2_path_with_the_token():
    seen: list[httpx.Request] = []

    secrets = read_vault_secrets(
        "http://vault:8200",
        "dev-only-token",
        "secret/el-regista",
        _client(200, SECRET_RESPONSE, seen),
    )

    assert secrets == {
        "database_url": "postgresql+psycopg://scouting:scouting@localhost:5433/scouting",
        "ingestion_api_key": "local-ingestion-key",
    }
    assert str(seen[0].url) == "http://vault:8200/v1/secret/data/el-regista"
    assert seen[0].headers["X-Vault-Token"] == "dev-only-token"


@pytest.mark.parametrize("status, body", [(403, MISSING_RESPONSE), (404, "{}")])
def test_a_refused_or_missing_secret_stops_the_start(status, body):
    with pytest.raises(VaultUnavailableError):
        read_vault_secrets(
            "http://vault:8200", "t", "secret/x", _client(status, body, [])
        )


def test_vault_that_does_not_answer_stops_the_start():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(VaultUnavailableError):
        read_vault_secrets("http://vault:8200", "t", "secret/x", client)


def _vault_returns(monkeypatch, secrets: dict[str, str]) -> list[str]:
    calls: list[str] = []

    def fake(address, token, path, client=None):
        calls.append(path)
        return secrets

    monkeypatch.setattr(vault, "read_vault_secrets", fake)
    monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
    monkeypatch.setenv("VAULT_TOKEN", "dev-only-token")
    return calls


def test_with_vault_configured_the_settings_come_from_vault(monkeypatch):
    _vault_returns(
        monkeypatch,
        {"ingestion_api_key": "from-vault", "database_url": "postgres://u:p@h/db"},
    )

    assert ApiSettings(_env_file=None).ingestion_api_key == "from-vault"
    # The usual normalisation still applies to what Vault gives.
    assert Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@h/db"


def test_an_environment_variable_wins_over_vault(monkeypatch):
    _vault_returns(monkeypatch, {"ingestion_api_key": "from-vault"})
    monkeypatch.setenv("INGESTION_API_KEY", "from-env")

    assert ApiSettings(_env_file=None).ingestion_api_key == "from-env"


def test_the_secret_path_can_be_chosen(monkeypatch):
    calls = _vault_returns(monkeypatch, {})
    monkeypatch.setenv("VAULT_SECRET_PATH", "secret/other")

    ApiSettings(_env_file=None)

    assert calls == ["secret/other"]


def test_without_vault_nothing_is_asked_production_reads_the_environment(
    monkeypatch,
):
    calls = _vault_returns(monkeypatch, {"ingestion_api_key": "from-vault"})
    monkeypatch.delenv("VAULT_ADDR")

    settings = ApiSettings(_env_file=None)

    assert calls == []
    assert settings.ingestion_api_key == ""
