"""
Fesium - Database Module
Handles SQLite database queries with transaction handling and read-only mode support.
Includes table name validation for safe dynamic queries.
"""

import logging
import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, List, Optional, Tuple

from fesium.core.config import trace_execution


logger = logging.getLogger(__name__)


def is_read_query(query: str) -> bool:
    """
    Safely detect if query is read-only.
    Handles injection tricks like ';;;SELECT * FROM users;'
    """
    cleaned = query.lstrip("; \t\n")

    while cleaned.startswith("--") or cleaned.startswith("/*"):
        if cleaned.startswith("--"):
            newline = cleaned.find("\n")
            cleaned = cleaned[newline + 1 :] if newline != -1 else ""
        elif cleaned.startswith("/*"):
            end = cleaned.find("*/")
            cleaned = cleaned[end + 2 :] if end != -1 else ""
        cleaned = cleaned.lstrip("; \t\n")

    if not cleaned:
        return True

    first_word = cleaned.split()[0].upper() if cleaned.split() else ""
    read_only_keywords = {"SELECT", "PRAGMA", "EXPLAIN", "WITH"}
    return first_word in read_only_keywords


TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_table_name(table_name: str) -> bool:
    """Validate that a table name is safe to use in SQL."""
    return bool(TABLE_NAME_PATTERN.match(table_name))


class DatabaseManager:
    """
    SQLite database manager with proper transaction handling.
    Uses context manager pattern for safe transactions.
    """

    def __init__(self, db_path: str = None, read_only: bool = True):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
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

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
    def execute(self, query: str, params: tuple = ()) -> Tuple[bool, Any]:
        """Execute a SQL query with proper transaction handling."""
        if not self.db_path:
            return False, "No database selected"

        if not os.path.exists(self.db_path):
            return False, f"Database file not found: {self.db_path}"

        is_read = is_read_query(query)

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

        except sqlite3.Error as exc:
            logger.error("SQL Error: %s", exc)
            return False, str(exc)
        except Exception as exc:
            logger.error("Database error: %s", exc)
            return False, str(exc)

    @trace_execution
    def list_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        success, result = self.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        if success:
            return [row[0] for row in result["rows"]]
        return []

    def get_table_info(self, table_name: str) -> List[dict]:
        """Get column info for a table."""
        if not validate_table_name(table_name):
            logger.warning("Invalid table name rejected: %s", table_name)
            return []

        success, result = self.execute(f"PRAGMA table_info({table_name})")
        if success:
            return [
                {
                    "name": row[1],
                    "type": row[2],
                    "nullable": not row[3],
                    "primary_key": bool(row[5]),
                }
                for row in result["rows"]
            ]
        return []
