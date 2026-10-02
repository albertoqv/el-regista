"""Data-only backup in pg_dump's own format: one COPY block per table.

The database is only reachable inside Railway's network, so the API streams the
dump and a GitHub Action stores it. Restore on an empty schema
(`alembic upgrade head`) with `psql -f backup.sql` or with `restore_data`.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import psycopg
from psycopg import sql
from sqlalchemy import Integer

from player_scouting.infrastructure.persistence.models import Base

END_OF_DATA = b"\\.\n"


def _copy_target(table_name: str, columns: list[str]) -> sql.Composed:
    return sql.SQL("COPY {} ({})").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )


def dump_data(connection: psycopg.Connection) -> Iterator[bytes]:
    """Tables in foreign-key order, so replaying the file top to bottom works."""
    yield b"-- El Regista: datos. Restaurar tras `alembic upgrade head`.\n\n"
    with connection.cursor() as cursor:
        for table in Base.metadata.sorted_tables:
            target = _copy_target(table.name, [column.name for column in table.columns])
            yield f"{target.as_string(connection)} FROM stdin;\n".encode()
            with cursor.copy(sql.SQL("{} TO STDOUT").format(target)) as copy:
                for block in copy:
                    yield bytes(block)
            yield END_OF_DATA + b"\n"


def restore_data(connection: psycopg.Connection, lines: Iterable[bytes]) -> None:
    """Replaces every table's rows with the dump's (same transaction as the caller)."""
    tables = Base.metadata.sorted_tables
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(sql.Identifier(table.name) for table in tables)
            )
        )
        rows = iter(lines)
        for line in rows:
            if not line.startswith(b"COPY "):
                continue
            statement = line.decode().strip().removesuffix(";")
            with cursor.copy(statement.encode()) as copy:
                for row in rows:
                    if row == END_OF_DATA:
                        break
                    copy.write(row)
        # Serial ids continue after the restored rows, not from 1.
        for table in tables:
            keys = list(table.primary_key.columns)
            if len(keys) != 1 or not isinstance(keys[0].type, Integer):
                continue
            cursor.execute(
                sql.SQL(
                    "SELECT setval(pg_get_serial_sequence(%s, %s), max({column})) "
                    "FROM {table} HAVING max({column}) IS NOT NULL"
                ).format(
                    column=sql.Identifier(keys[0].name),
                    table=sql.Identifier(table.name),
                ),
                (table.name, keys[0].name),
            )
