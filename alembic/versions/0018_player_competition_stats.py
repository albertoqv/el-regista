"""a player's numbers per competition and season (Europe, cups, national teams)

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "player_competition_stats",
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.player_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("competition", sa.String(), primary_key=True),
        sa.Column("season_label", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("appearances", sa.Integer(), nullable=False),
        sa.Column("goals", sa.Integer(), nullable=False),
        sa.Column("assists", sa.Integer(), nullable=False),
        sa.Column("minutes_played", sa.Integer(), nullable=False),
        sa.Column("yellow_cards", sa.Integer(), nullable=False),
        sa.Column("red_cards", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("player_competition_stats")
