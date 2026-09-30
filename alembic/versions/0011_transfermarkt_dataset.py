"""transfermarkt id, height and detailed position on players

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("transfermarkt_id", sa.Integer(), nullable=True))
    op.add_column("players", sa.Column("height_cm", sa.Integer(), nullable=True))
    op.add_column("players", sa.Column("detailed_position", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_players_transfermarkt_id", "players", ["transfermarkt_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_players_transfermarkt_id", "players")
    op.drop_column("players", "detailed_position")
    op.drop_column("players", "height_cm")
    op.drop_column("players", "transfermarkt_id")
