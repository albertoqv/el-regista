from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiFootballSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_football_key: str = ""


@lru_cache
def get_api_football_settings() -> ApiFootballSettings:
    return ApiFootballSettings()
