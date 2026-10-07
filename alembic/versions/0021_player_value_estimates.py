"""market value estimated by the model, with its factors, and the model's error

Revision ID: 0021
Revises: 0020
Create Date: 2026-10-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "player_value_estimates",
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.player_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("estimate_eur", sa.BigInteger(), nullable=False),
        sa.Column("factors", sa.String(), nullable=False),
        sa.Column("computed_on", sa.Date(), nullable=False),
    )
    op.create_table(
        "value_model",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("computed_on", sa.Date(), nullable=False),
        sa.Column("samples", sa.Integer(), nullable=False),
        sa.Column("median_error", sa.Float(), nullable=False),
        sa.Column("average_eur", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("value_model")
    op.drop_table("player_value_estimates")
