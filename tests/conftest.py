import pytest

from player_scouting.presentation.api.read_cache import READ_CACHE
from player_scouting.presentation.api.settings import get_api_settings

# Variables a developer machine may carry (the home sync stores the ingestion key)
# must not change how the API behaves under test.
_MACHINE_VARIABLES = (
    "INGESTION_API_KEY",
    "REQUIRE_INGESTION_KEY",
    "EXPOSE_DOCS",
    "RATE_LIMIT_PER_MINUTE",
    "VERCEL",
    "VAULT_ADDR",
    "VAULT_TOKEN",
    "VAULT_SECRET_PATH",
)


@pytest.fixture(autouse=True)
def _isolated_api_settings(monkeypatch):
    for name in _MACHINE_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    get_api_settings.cache_clear()
    READ_CACHE.clear()
    yield
    get_api_settings.cache_clear()
    READ_CACHE.clear()
