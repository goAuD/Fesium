"""The engine boundary behind the Database view.

``DatabaseManager`` owns the read-only gate, the risk classification, the
transaction handling and the result shape the views consume. Everything that
differs between SQL engines lives here: connecting, availability, schema
inspection queries, the driver's error type and each dialect's read verbs.

``sqlite3`` is imported at module level because it ships with Python.
``pymysql`` is deliberately never imported here at module level - the MySQL
engine imports it inside the method that connects, so a SQLite-only user
never needs the package installed.
"""

import os
import sqlite3
from typing import Any, Protocol

from fesium.core.security import classify_query_risk, strip_sql_leading_noise

SQLITE_READ_VERBS = frozenset({"SELECT", "PRAGMA", "EXPLAIN", "WITH"})
MYSQL_READ_VERBS = frozenset({"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN", "WITH"})


def query_is_read(query: str, read_verbs: frozenset[str]) -> bool:
    """
    Classify a query as read-only against a dialect's verb set.

    Handles injection tricks like ';;;SELECT * FROM users;' and leading
    comments that would otherwise mask the real first keyword. The
    destructive-body check for WITH applies on every engine: keyword gating
    must not be bypassable through a CTE on a dialect whose extra verbs we do
    not list.
    """
    body = strip_sql_leading_noise(query)
    if not body:
        return True

    words = body.split()
    first_word = words[0].upper() if words else ""

    if first_word == "WITH" and classify_query_risk(query).requires_confirmation:
        # WITH CTE that contains a destructive body - not read-only.
        return False

    return first_word in read_verbs


class DatabaseEngine(Protocol):
    """Everything about a SQL engine that DatabaseManager cannot know.

    ``target`` is what the manager was pointed at: a file path for SQLite,
    a database name for MySQL.
    """

    placeholder: str
    read_verbs: frozenset[str]
    errors: tuple[type[BaseException], ...]

    def connect(self, target: str, *, read_only: bool) -> Any:
        """Open a connection to the engine."""
        ...

    def availability_error(self, target: str) -> str | None:
        """Why the target cannot be reached at all, or None if it might be."""
        ...

    def list_tables_query(self) -> tuple[str, tuple]:
        """The query that lists browseable tables, with bound parameters."""
        ...

    def table_columns_query(self, table_name: str) -> tuple[str, tuple]:
        """The query that describes one table's columns, name bound."""
        ...

    def interpret_column_rows(self, rows: list[tuple]) -> list[dict]:
        """Map the driver's column rows onto the shared column dict shape."""
        ...


class SqliteEngine:
    """SQLite support. Ships with Python, so there is nothing to install."""

    placeholder = "?"
    read_verbs = SQLITE_READ_VERBS
    errors = (sqlite3.Error,)

    def connect(self, target: str, *, read_only: bool) -> Any:
        conn = sqlite3.connect(target)
        conn.row_factory = sqlite3.Row
        return conn

    def availability_error(self, target: str) -> str | None:
        if not os.path.exists(target):
            return f"Database file not found: {target}"
        return None

    def list_tables_query(self) -> tuple[str, tuple]:
        # SQLite reserves the ``sqlite_`` prefix for internal tables such as
        # ``sqlite_sequence`` and ``sqlite_stat1``. They are noise in a schema
        # browser. GLOB is used rather than LIKE because ``_`` is a literal in
        # a GLOB pattern but a single-character wildcard in LIKE.
        return (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT GLOB 'sqlite_*' "
            "ORDER BY name",
            (),
        )

    def table_columns_query(self, table_name: str) -> tuple[str, tuple]:
        # pragma_table_info() is the table-valued form of `PRAGMA table_info`,
        # so the table name travels as a bound parameter instead of being
        # formatted into the SQL string.
        return ("SELECT * FROM pragma_table_info(?)", (table_name,))

    def interpret_column_rows(self, rows: list[tuple]) -> list[dict]:
        return [
            {
                "name": row[1],
                "type": row[2],
                "nullable": not row[3],
                "primary_key": bool(row[5]),
            }
            for row in rows
        ]
