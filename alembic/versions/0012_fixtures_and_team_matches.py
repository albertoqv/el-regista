"""fixtures and per-team match metrics

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fixtures",
        sa.Column("match_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("kickoff", sa.DateTime(), nullable=False),
        sa.Column("home_team", sa.String(), nullable=False),
        sa.Column("away_team", sa.String(), nullable=False),
        sa.Column("home_goals", sa.Integer(), nullable=True),
        sa.Column("away_goals", sa.Integer(), nullable=True),
        sa.Column("home_xg", sa.Float(), nullable=True),
        sa.Column("away_xg", sa.Float(), nullable=True),
    )
    op.create_index("ix_fixtures_competition", "fixtures", ["competition"])
    op.create_index("ix_fixtures_kickoff", "fixtures", ["kickoff"])
    op.create_table(
        "team_matches",
        sa.Column("match_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("team", sa.String(), primary_key=True),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("played_on", sa.Date(), nullable=False),
        sa.Column("opponent", sa.String(), nullable=False),
        sa.Column("home", sa.Boolean(), nullable=False),
        sa.Column("goals_for", sa.Integer(), nullable=False),
        sa.Column("goals_against", sa.Integer(), nullable=False),
        sa.Column("xg_for", sa.Float(), nullable=False),
        sa.Column("xg_against", sa.Float(), nullable=False),
        sa.Column("npxg_for", sa.Float(), nullable=False),
        sa.Column("npxg_against", sa.Float(), nullable=False),
        sa.Column("ppda", sa.Float(), nullable=True),
        sa.Column("ppda_allowed", sa.Float(), nullable=True),
        sa.Column("deep", sa.Integer(), nullable=False),
        sa.Column("deep_allowed", sa.Integer(), nullable=False),
        sa.Column("xpts", sa.Float(), nullable=False),
        sa.Column("result", sa.String(), nullable=False),
    )
    op.create_index("ix_team_matches_season_label", "team_matches", ["season_label"])


def downgrade() -> None:
    op.drop_table("team_matches")
    op.drop_table("fixtures")
