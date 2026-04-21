import os
import tempfile

from fesium.core.database import (
    DatabaseManager,
    build_table_preview_query,
    is_read_query,
    validate_table_name,
)


def test_is_read_query_blocks_write_keywords():
    assert is_read_query("SELECT * FROM users") is True
    assert is_read_query("DELETE FROM users") is False


def test_is_read_query_sees_through_leading_comments():
    assert is_read_query("-- comment\nSELECT 1") is True
    assert is_read_query("/* block */ DELETE FROM users") is False


def test_is_read_query_flags_with_cte_containing_destructive_keyword():
    # Pure SELECT CTE stays read-only.
    assert is_read_query(
        "WITH recent AS (SELECT id FROM users LIMIT 10) SELECT * FROM recent"
    ) is True
    # CTE that hides a write — read-only mode must still block it.
    assert is_read_query(
        "WITH doomed AS (SELECT id FROM users) DELETE FROM users WHERE id IN (SELECT id FROM doomed)"
    ) is False


def test_validate_table_name_rejects_injection_shapes():
    assert validate_table_name("users") is True
    assert validate_table_name("drop;users") is False


def test_database_manager_defaults_to_read_only_mode():
    db = DatabaseManager()
    assert db.read_only is True


def test_database_manager_read_only_mode_blocks_write_queries():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as handle:
        db_path = handle.name

    try:
        db = DatabaseManager(db_path, read_only=False)
        ok, _ = db.execute("CREATE TABLE test (id INTEGER)")
        assert ok is True

        db.read_only = True
        ok, message = db.execute("INSERT INTO test VALUES (1)")
        assert ok is False
        assert "Read-only mode" in message
    finally:
        os.remove(db_path)


def test_build_table_preview_query_uses_limit_and_rejects_invalid_name():
    assert build_table_preview_query("users", limit=25) == "SELECT * FROM users LIMIT 25"

    try:
        build_table_preview_query("users;drop", limit=10)
    except ValueError as exc:
        assert "Invalid table name" in str(exc)
    else:
        raise AssertionError("expected ValueError for invalid table name")
