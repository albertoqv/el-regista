from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://scouting:scouting@localhost:5432/scouting"

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
