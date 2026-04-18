import os
import tempfile

from fesium.core.database import DatabaseManager, is_read_query, validate_table_name


def test_is_read_query_blocks_write_keywords():
    assert is_read_query("SELECT * FROM users") is True
    assert is_read_query("DELETE FROM users") is False


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
