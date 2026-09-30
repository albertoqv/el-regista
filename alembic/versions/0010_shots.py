"""understat matches and shots

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "understat_matches",
        sa.Column("match_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("played_on", sa.Date(), nullable=False),
        sa.Column("home_team", sa.String(), nullable=False),
        sa.Column("away_team", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_understat_matches_season_label", "understat_matches", ["season_label"]
    )
    op.create_table(
        "shots",
        sa.Column("shot_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("understat_matches.match_id"),
            nullable=False,
        ),
        sa.Column("understat_player_id", sa.Integer(), nullable=False),
        sa.Column("player_name", sa.String(), nullable=False),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("xg", sa.Float(), nullable=False),
        sa.Column("situation", sa.String(), nullable=False),
        sa.Column("shot_type", sa.String(), nullable=False),
        sa.Column("home", sa.Boolean(), nullable=False),
        sa.Column("assisted_by", sa.String(), nullable=True),
        sa.Column("decisive", sa.Boolean(), nullable=False),
        sa.Column("outside_box", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_shots_match_id", "shots", ["match_id"])
    op.create_index("ix_shots_understat_player_id", "shots", ["understat_player_id"])
    op.create_index("ix_players_understat_id", "players", ["understat_id"])


def downgrade() -> None:
    op.drop_index("ix_players_understat_id", "players")
    op.drop_table("shots")
    op.drop_table("understat_matches")
