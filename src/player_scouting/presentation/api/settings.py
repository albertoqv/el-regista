from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from player_scouting.infrastructure.secrets.vault import sources_with_vault


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = "http://localhost:3000"
    ingestion_api_key: str = ""
    # Secret mixed into the daily visitor hash (falls back to the ingestion key).
    visit_salt: str = ""
    # Optional: show the server bill in the admin panel (Railway workspace token).
    railway_api_token: str = ""
    railway_workspace_id: str = ""
    # Optional: the database's monthly transfer in the admin panel (Neon API key).
    neon_api_key: str = ""
    neon_project_id: str = ""
    # Production fails closed: no key configured = no ingestion. Vercel sets VERCEL=1,
    # so a deployment there is production unless the variables say otherwise.
    require_ingestion_key: bool = Field(default_factory=lambda: "VERCEL" in os.environ)
    # Interactive API map at /docs; off in production (it lists every endpoint).
    expose_docs: bool = Field(default_factory=lambda: "VERCEL" not in os.environ)
    # Requests per minute from one address before answering 429.
    rate_limit_per_minute: int = 600

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Locally (Docker Compose) the secrets can come from Vault; see vault.py.
        return sources_with_vault(
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_api_settings() -> ApiSettings:
    return ApiSettings()
