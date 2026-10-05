from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from player_scouting.infrastructure.secrets.vault import sources_with_vault


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://scouting:scouting@localhost:5432/scouting"

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

    @field_validator("database_url")
    @classmethod
    def _with_driver(cls, url: str) -> str:
        """Hosted Postgres (Neon, Supabase) gives postgres:// URLs: name the driver."""
        for scheme in ("postgresql://", "postgres://"):
            if url.startswith(scheme):
                return "postgresql+psycopg://" + url.removeprefix(scheme)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
