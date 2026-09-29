"""add extended statistics columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

INT_COLUMNS = (
    "shots",
    "shots_on_target",
    "passes_completed",
    "passes_attempted",
    "key_passes",
    "dribbles_completed",
    "dribbles_attempted",
    "tackles_won",
    "interceptions",
    "fouls_committed",
    "fouls_won",
    "yellow_cards",
    "red_cards",
)


def upgrade() -> None:
    for column_name in INT_COLUMNS:
        op.add_column(
            "players",
            sa.Column(
                column_name, sa.Integer(), nullable=False, server_default="0"
            ),
        )
    op.add_column(
        "players",
        sa.Column(
            "expected_goals",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )


def downgrade() -> None:
    op.drop_column("players", "expected_goals")
    for column_name in INT_COLUMNS:
        op.drop_column("players", column_name)
