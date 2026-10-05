"""Secrets from HashiCorp Vault (KV v2), for the local Docker Compose setup.

When `VAULT_ADDR` is set, the settings ask Vault for the path in `VAULT_SECRET_PATH`
(default `secret/el-regista`) with the token in `VAULT_TOKEN`, and use its keys
(`database_url`, `ingestion_api_key`, ...) for the fields of the same name.
Environment variables still win, and without `VAULT_ADDR` nothing is asked: that is
how production runs (Vercel and GitHub hold the secrets as variables).
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

DEFAULT_SECRET_PATH = "secret/el-regista"


class VaultUnavailableError(RuntimeError):
    """Vault was configured but did not give the secrets: better not to start."""


def read_vault_secrets(
    address: str, token: str, path: str, client: httpx.Client | None = None
) -> dict[str, str]:
    # KV v2 reads live under <mount>/data/<name>.
    mount, _, name = path.strip("/").partition("/")
    url = f"{address.rstrip('/')}/v1/{mount}/data/{name}"
    http = client or httpx.Client(timeout=5)
    try:
        response = http.get(url, headers={"X-Vault-Token": token})
    except httpx.HTTPError as error:
        raise VaultUnavailableError(f"Vault at {address} is not answering") from error
    if response.status_code != 200:
        raise VaultUnavailableError(
            f"Vault refused {path}: HTTP {response.status_code}"
        )
    return dict(response.json()["data"]["data"])


class VaultSettingsSource(PydanticBaseSettingsSource):
    """A settings source below the environment: fills what the variables leave out."""

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        address = os.environ.get("VAULT_ADDR")
        if not address:
            return {}
        secrets = read_vault_secrets(
            address,
            os.environ.get("VAULT_TOKEN", ""),
            os.environ.get("VAULT_SECRET_PATH", DEFAULT_SECRET_PATH),
        )
        fields = self.settings_cls.model_fields
        return {key: value for key, value in secrets.items() if key in fields}


def sources_with_vault(
    settings_cls: type[BaseSettings],
    init_settings: PydanticBaseSettingsSource,
    env_settings: PydanticBaseSettingsSource,
    dotenv_settings: PydanticBaseSettingsSource,
    file_secret_settings: PydanticBaseSettingsSource,
) -> tuple[PydanticBaseSettingsSource, ...]:
    """Priority: arguments, environment, .env file, Vault, secret files."""
    return (
        init_settings,
        env_settings,
        dotenv_settings,
        VaultSettingsSource(settings_cls),
        file_secret_settings,
    )
