"""per-player match lines (Understat rosters)

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "player_match_stats",
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("understat_matches.match_id"),
            primary_key=True,
        ),
        sa.Column("understat_player_id", sa.Integer(), primary_key=True),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("played_on", sa.Date(), nullable=False),
        sa.Column("team", sa.String(), nullable=False),
        sa.Column("opponent", sa.String(), nullable=False),
        sa.Column("home", sa.Boolean(), nullable=False),
        sa.Column("player_name", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=False),
        *[
            sa.Column(name, sa.Integer(), nullable=False)
            for name in (
                "minutes",
                "goals",
                "own_goals",
                "assists",
                "shots",
                "key_passes",
            )
        ],
        sa.Column("xg", sa.Float(), nullable=False),
        sa.Column("xa", sa.Float(), nullable=False),
        sa.Column("yellow", sa.Integer(), nullable=False),
        sa.Column("red", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_player_match_stats_season_label", "player_match_stats", ["season_label"]
    )
    op.create_index("ix_player_match_stats_team", "player_match_stats", ["team"])


def downgrade() -> None:
    op.drop_table("player_match_stats")
