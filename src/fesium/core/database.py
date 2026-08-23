"""
Fesium - Database Module
Handles database queries with transaction handling and read-only mode support.

Engine-specific behaviour lives in ``database_engines``. This module keeps
what is engine-neutral: the read-only gate, the risk-aware classification,
transaction handling, ``validate_table_name`` and the result shape the views
consume.
"""

import logging
import re
from contextlib import contextmanager
from typing import Any

from fesium.core.config import trace_execution
from fesium.core.database_engines import SqliteEngine, query_is_read

logger = logging.getLogger(__name__)


def is_read_query(query: str) -> bool:
    """
    Safely detect if query is read-only against SQLite's verb set.

    Handles injection tricks like ';;;SELECT * FROM users;' and leading
    comments that would otherwise mask the real first keyword. Engines with
    other read verbs classify through ``query_is_read`` instead.
    """
    return query_is_read(query, SqliteEngine.read_verbs)


TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_table_name(table_name: str) -> bool:
    """Validate that a table name is safe to use in SQL."""
    return bool(TABLE_NAME_PATTERN.match(table_name))


def build_table_preview_query(table_name: str, *, limit: int = 100) -> str:
    """Build a safe preview query for a known table.

    The name is validated rather than quoted: ``validate_table_name`` admits
    only ``[A-Za-z_][A-Za-z0-9_]*``, which needs no quoting on any engine
    this module supports.
    """
    if not validate_table_name(table_name):
        raise ValueError(f"Invalid table name: {table_name}")

    resolved_limit = max(1, int(limit))
    return f"SELECT * FROM {table_name} LIMIT {resolved_limit}"


class DatabaseManager:
    """
    Database manager with proper transaction handling.
    Uses context manager pattern for safe transactions. SQL engine specifics
    are delegated to a DatabaseEngine (SQLite by default).
    """

    def __init__(self, db_path: str = None, read_only: bool = True, engine: Any | None = None):
        self.db_path = db_path
        self._engine = engine if engine is not None else SqliteEngine()
        self._connection: Any | None = None
        self.read_only = read_only

    def set_database(self, db_path: str) -> None:
        """Set the database path."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self.db_path = db_path
        logger.info("Database set to: %s", db_path)

    @contextmanager
    def connection(self):
        """Context manager for database connection."""
        if not self.db_path:
            raise ValueError("No database path set")

        conn = self._engine.connect(self.db_path, read_only=self.read_only)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        with self.connection() as conn:
            try:
                yield conn
                conn.commit()
                logger.debug("Transaction committed")
            except Exception as exc:
                conn.rollback()
                logger.error("Transaction rolled back: %s", exc)
                raise

    @trace_execution
    def execute(self, query: str, params: tuple = ()) -> tuple[bool, Any]:
        """Execute a SQL query with proper transaction handling."""
        if not self.db_path:
            return False, "No database selected"

        unavailable = self._engine.availability_error(self.db_path)
        if unavailable:
            return False, unavailable

        is_read = query_is_read(query, self._engine.read_verbs)

        if self.read_only and not is_read:
            return False, "Read-only mode: Write operations are disabled"

        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                if is_read:
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    result = {
                        "columns": columns,
                        "rows": [tuple(row) for row in rows],
                        "count": len(rows),
                    }
                    logger.info("SELECT returned %s rows", len(rows))
                    return True, result

                conn.commit()
                affected = cursor.rowcount
                logger.info("Query affected %s rows", affected)
                return True, {"affected": affected}

        except self._engine.errors as exc:
            logger.error("SQL Error: %s", exc)
            return False, str(exc)
        except Exception as exc:
            logger.error("Database error: %s", exc)
            return False, str(exc)

    @trace_execution
    def list_tables(self) -> list[str]:
        """List the browseable tables, skipping the engine's own bookkeeping.

        What counts as bookkeeping is engine knowledge - see
        ``SqliteEngine.list_tables_query`` for the SQLite side.
        """
        sql, params = self._engine.list_tables_query()
        success, result = self.execute(sql, params)
        if success:
            return [row[0] for row in result["rows"]]
        return []

    def get_table_info(self, table_name: str) -> list[dict]:
        """Get column info for a table."""
        if not validate_table_name(table_name):
            logger.warning("Invalid table name rejected: %s", table_name)
            return []

        # The engine supplies a query that takes the table name as a bound
        # parameter, never formatted into the SQL string.
        sql, params = self._engine.table_columns_query(table_name)
        success, result = self.execute(sql, params)
        if success:
            return self._engine.interpret_column_rows(result["rows"])
        return []
