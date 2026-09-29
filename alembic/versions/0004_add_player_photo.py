"""add photo_url to players

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-29

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("players", sa.Column("photo_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "photo_url")
