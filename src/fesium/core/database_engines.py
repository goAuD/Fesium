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
    extra_destructive_verbs: frozenset[str]
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
    # SQLite's destructive vocabulary is the shared one; it adds nothing.
    extra_destructive_verbs = frozenset()
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


# Long enough for a busy local server to answer, short enough that a dead
# host cannot freeze the UI. probe_database() answers "is anything there"
# first; this bounds the connect attempt that follows it.
MYSQL_CONNECT_TIMEOUT_SECONDS = 5


class MySQLEngine:
    """MySQL support over PyMySQL.

    The driver is imported lazily inside the methods that need it: a
    SQLite-only user never has to install pymysql for Fesium to work.
    ``connector`` is injectable so the test suite can hand in a fake and
    never open a socket.
    """

    placeholder = "%s"
    read_verbs = MYSQL_READ_VERBS
    # Verbs that change state on MySQL and mean nothing to SQLite, which is
    # why the shared destructive list has never carried them. Read-only mode
    # already refuses all of them, because it admits only `read_verbs`. Write
    # mode gates on confirmation instead, and that gate was blind to every one
    # of these until they were wired into `classify_query_risk`.
    #
    # CREATE is deliberately absent. Creating a table removes nothing, and a
    # prompt warning that the query "may modify or remove data" would be a lie
    # the user quickly learns to click through - which is how a confirmation
    # dialog stops working at all.
    extra_destructive_verbs = frozenset({"CALL", "GRANT", "REVOKE", "RENAME", "LOAD"})

    def __init__(
        self,
        *,
        host: str,
        port: int = 3306,
        user: str,
        password: str,
        connect_timeout: int = MYSQL_CONNECT_TIMEOUT_SECONDS,
        connector=None,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password  # session memory only - never persisted
        self.connect_timeout = connect_timeout
        self._connector = connector

    @property
    def errors(self) -> tuple[type[BaseException], ...]:
        import pymysql

        return (pymysql.MySQLError,)

    def connect(self, target: str, *, read_only: bool):
        import pymysql

        connector = self._connector if self._connector is not None else pymysql.connect
        conn = connector(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=target or None,
            charset="utf8mb4",
            connect_timeout=self.connect_timeout,
        )
        if read_only:
            # Keyword gating alone is trivially bypassed on a dialect it does
            # not know, so the session itself is pinned read-only too.
            with conn.cursor() as cursor:
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
        return conn

    def availability_error(self, target: str) -> str | None:
        # A MySQL target is not a file. The bounded connect attempt is the
        # availability check; its failure surfaces as a connection error.
        return None

    def list_tables_query(self) -> tuple[str, tuple]:
        # information_schema for the current schema; DATABASE() names the
        # schema so nothing is interpolated into the SQL string.
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() ORDER BY table_name",
            (),
        )

    def table_columns_query(self, table_name: str) -> tuple[str, tuple]:
        # Same posture as pragma_table_info(?): the table name travels as a
        # bound parameter instead of being formatted into the SQL string.
        return (
            "SELECT column_name, column_type, is_nullable, column_key "
            "FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s "
            "ORDER BY ordinal_position",
            (table_name,),
        )

    def interpret_column_rows(self, rows: list[tuple]) -> list[dict]:
        return [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "primary_key": row[3] == "PRI",
            }
            for row in rows
        ]

