"""add player_season_statistics and drop stats from players

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

INT_COLUMNS = (
    "goals",
    "assists",
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
    op.create_table(
        "player_season_statistics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.player_id"),
            nullable=False,
        ),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        *(
            sa.Column(column_name, sa.Integer(), nullable=False, server_default="0")
            for column_name in INT_COLUMNS
        ),
        sa.Column(
            "expected_goals", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.UniqueConstraint("player_id", "competition", "season_label"),
    )

    for column_name in (*INT_COLUMNS, "expected_goals"):
        op.drop_column("players", column_name)


def downgrade() -> None:
    for column_name in INT_COLUMNS:
        op.add_column(
            "players",
            sa.Column(column_name, sa.Integer(), nullable=False, server_default="0"),
        )
    op.add_column(
        "players",
        sa.Column("expected_goals", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.drop_table("player_season_statistics")
