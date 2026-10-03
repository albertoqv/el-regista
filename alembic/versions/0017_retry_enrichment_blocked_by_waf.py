"""Players marked "not found" while Transfermarkt's WAF blocked the runner.

On 2026-10-03 the refresh read Transfermarkt's bot challenge (an empty 202) as
empty search results and marked about 400 players as checked without data.
Unmark the ones still without a photo so they are looked up again.

Revision ID: 0017
Revises: 0016
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE players SET enrichment_checked_at = NULL "
        "WHERE enrichment_checked_at >= '2026-10-03' AND photo_url IS NULL"
    )


def downgrade() -> None:
    # Nothing to restore: the marks were wrong.
    pass
