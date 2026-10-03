from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_origins: str = "http://localhost:3000"
    ingestion_api_key: str = ""
    # Secret mixed into the daily visitor hash (falls back to the ingestion key).
    visit_salt: str = ""
    # Optional: show the server bill in the admin panel (Railway workspace token).
    railway_api_token: str = ""
    railway_workspace_id: str = ""
    # Production (the Dockerfile) fails closed: no key configured = no ingestion.
    require_ingestion_key: bool = False
    # Interactive API map at /docs; off in production (it lists every endpoint).
    expose_docs: bool = True
    # Requests per minute from one address before answering 429.
    rate_limit_per_minute: int = 600

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_api_settings() -> ApiSettings:
    return ApiSettings()
