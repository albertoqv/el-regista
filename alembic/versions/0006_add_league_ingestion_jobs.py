"""add league_ingestion_jobs table

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "league_ingestion_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("league_id", sa.Integer(), nullable=False),
        sa.Column("league_name", sa.String(), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("next_page", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_pages", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("league_ingestion_jobs")
