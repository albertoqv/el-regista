"""make date_of_birth optional and add birth_year

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-30

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("players", "date_of_birth", nullable=True)
    op.add_column("players", sa.Column("birth_year", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "birth_year")
    op.alter_column("players", "date_of_birth", nullable=False)
