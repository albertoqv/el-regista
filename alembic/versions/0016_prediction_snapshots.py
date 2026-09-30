"""forecasts logged before kickoff (track record)

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prediction_snapshots",
        sa.Column("match_id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("competition", sa.String(), nullable=False),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("kickoff", sa.DateTime(), nullable=False),
        sa.Column("home_team", sa.String(), nullable=False),
        sa.Column("away_team", sa.String(), nullable=False),
        sa.Column("made_at", sa.DateTime(), nullable=False),
        sa.Column("model_home", sa.Float(), nullable=False),
        sa.Column("model_draw", sa.Float(), nullable=False),
        sa.Column("model_away", sa.Float(), nullable=False),
        sa.Column("market_home", sa.Float(), nullable=True),
        sa.Column("market_draw", sa.Float(), nullable=True),
        sa.Column("market_away", sa.Float(), nullable=True),
        sa.Column("over_2_5", sa.Float(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("prediction_snapshots")
