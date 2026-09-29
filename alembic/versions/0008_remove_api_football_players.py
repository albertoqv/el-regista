"""remove players ingested from API-Football

FBref (via Kaggle) replaces API-Football as the data source and covers all of
these players under their full names, so keeping them would duplicate them.
API-Football players are the only ones whose photo comes from its media CDN.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

API_FOOTBALL_PLAYERS = (
    "SELECT player_id FROM players "
    "WHERE photo_url LIKE 'https://media.api-sports.io/%'"
)


def upgrade() -> None:
    for table in ("player_market_values", "player_season_statistics"):
        op.execute(f"DELETE FROM {table} WHERE player_id IN ({API_FOOTBALL_PLAYERS})")
    op.execute(f"DELETE FROM players WHERE player_id IN ({API_FOOTBALL_PLAYERS})")
    op.execute("DELETE FROM league_ingestion_jobs")


def downgrade() -> None:
    # Deleted rows cannot be restored; re-ingest from API-Football if needed.
    pass
