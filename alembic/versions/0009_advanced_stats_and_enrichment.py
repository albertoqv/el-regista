"""advanced stats table, team/minutes per season, understat id and enrichment marker

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("understat_id", sa.Integer(), nullable=True))
    op.add_column(
        "players",
        sa.Column("enrichment_checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "player_season_statistics",
        sa.Column("minutes_played", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "player_season_statistics", sa.Column("team", sa.String(), nullable=True)
    )
    op.create_table(
        "player_season_advanced_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.player_id"),
            nullable=False,
        ),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("expected_goals", sa.Float(), nullable=False),
        sa.Column("expected_assists", sa.Float(), nullable=False),
        sa.Column("key_passes", sa.Integer(), nullable=False),
        sa.Column("xg_chain", sa.Float(), nullable=False),
        sa.Column("xg_buildup", sa.Float(), nullable=False),
        sa.UniqueConstraint("player_id", "competition", "season_label"),
    )


def downgrade() -> None:
    op.drop_table("player_season_advanced_stats")
    op.drop_column("player_season_statistics", "team")
    op.drop_column("player_season_statistics", "minutes_played")
    op.drop_column("players", "enrichment_checked_at")
    op.drop_column("players", "understat_id")
