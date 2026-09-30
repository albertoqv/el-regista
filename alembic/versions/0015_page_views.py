"""anonymous page views for the admin panel

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "page_views",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("visitor", sa.String(), nullable=False),
        sa.Column("referrer", sa.String(), nullable=True),
    )
    op.create_index("ix_page_views_day", "page_views", ["day"])


def downgrade() -> None:
    op.drop_index("ix_page_views_day", table_name="page_views")
    op.drop_table("page_views")
