"""drop the dataset's Africa Cup lines labelled 2026 (Transfermarkt names it 2025)

Revision ID: 0019
Revises: 0018
Create Date: 2026-10-07

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # AFCON 2025 came twice: "2026" from the dataset, "2025" from Transfermarkt's
    # pages. Transfermarkt never writes 2026, so only the dataset's copy goes.
    op.execute(
        "DELETE FROM player_competition_stats"
        " WHERE competition = 'Copa África' AND season_label = '2026'"
    )


def downgrade() -> None:
    pass
