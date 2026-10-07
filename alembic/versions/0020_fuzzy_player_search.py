"""accent-insensitive, typo-tolerant player search (unaccent + pg_trgm)

Revision ID: 0020
Revises: 0019
Create Date: 2026-10-07

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # unaccent() depends on a dictionary setting, so Postgres does not let it be used
    # where an immutable function is required; this wrapper names the dictionary.
    op.execute(
        "CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text"
        " LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT"
        " AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
