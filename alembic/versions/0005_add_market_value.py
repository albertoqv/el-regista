"""add preferred_foot to players and player_market_values table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("preferred_foot", sa.String(), nullable=True))
    op.create_table(
        "player_market_values",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.player_id"),
            nullable=False,
        ),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("amount_eur", sa.Integer(), nullable=False),
        sa.Column("club", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("player_market_values")
    op.drop_column("players", "preferred_foot")
