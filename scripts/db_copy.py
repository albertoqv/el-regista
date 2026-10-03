"""Dumps the database to a .sql.gz file or restores one into it (data only).

The same COPY format as GET /ingestion/backup and `pg_dump --data-only`, through
the app's own dump/restore so no pg_dump of a matching version is needed.

    DATABASE_URL=... uv run python scripts/db_copy.py dump elregista.sql.gz
    DATABASE_URL=... uv run python scripts/db_copy.py restore elregista.sql.gz

Restore replaces every table's rows; run `alembic upgrade head` on the target first.
"""

from __future__ import annotations

import gzip
import sys

import psycopg

from player_scouting.infrastructure.persistence.backup import dump_data, restore_data
from player_scouting.infrastructure.persistence.settings import get_settings


def _libpq_url() -> str:
    return get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("dump", "restore"):
        print(__doc__)
        return 2
    command, path = sys.argv[1], sys.argv[2]
    with psycopg.connect(_libpq_url(), prepare_threshold=None) as connection:
        if command == "dump":
            with gzip.open(path, "wb") as file:
                for chunk in dump_data(connection):
                    file.write(chunk)
        else:
            with gzip.open(path, "rb") as file:
                restore_data(connection, file)
            connection.commit()
    print(f"{command}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
