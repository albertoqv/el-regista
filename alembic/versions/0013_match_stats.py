"""football-data.co.uk match stats and odds

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_COUNTS = (
    "goals",
    "goals_ht",
    "shots",
    "shots_on_target",
    "fouls",
    "corners",
    "yellows",
    "reds",
)
_ODDS = ("odds_home", "odds_draw", "odds_away", "odds_over_2_5", "odds_under_2_5")


def upgrade() -> None:
    op.create_table(
        "match_stats",
        sa.Column("competition", sa.String(), primary_key=True),
        sa.Column("played_on", sa.Date(), primary_key=True),
        sa.Column("home_team", sa.String(), primary_key=True),
        sa.Column("away_team", sa.String(), primary_key=True),
        sa.Column("season_label", sa.String(), nullable=False),
        sa.Column("referee", sa.String(), nullable=True),
        *[
            sa.Column(f"{side}_{name}", sa.Integer(), nullable=True)
            for name in _COUNTS
            for side in ("home", "away")
        ],
        *[sa.Column(name, sa.Float(), nullable=True) for name in _ODDS],
    )
    op.create_index("ix_match_stats_season_label", "match_stats", ["season_label"])


def downgrade() -> None:
    op.drop_table("match_stats")
