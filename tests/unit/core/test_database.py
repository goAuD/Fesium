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
    # CTE that hides a write - read-only mode must still block it.
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


def _seed_database(tmp_path):
    db_path = tmp_path / "schema.sqlite"
    # DatabaseManager only opens databases that already exist - it never
    # creates one - so the empty file has to be there first.
    db_path.touch()
    manager = DatabaseManager(str(db_path), read_only=False)
    ok, _ = manager.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, note TEXT)"
    )
    assert ok is True
    return str(db_path)


def test_get_table_info_reads_columns_without_interpolating_the_table_name(tmp_path):
    db = DatabaseManager(_seed_database(tmp_path), read_only=True)

    columns = db.get_table_info("users")

    assert [column["name"] for column in columns] == ["id", "name", "note"]
    assert columns[0] == {"name": "id", "type": "INTEGER", "nullable": True, "primary_key": True}
    assert columns[1]["nullable"] is False
    assert columns[2]["primary_key"] is False


def test_get_table_info_returns_empty_for_unknown_table(tmp_path):
    db = DatabaseManager(_seed_database(tmp_path), read_only=True)

    assert db.get_table_info("does_not_exist") == []


def test_get_table_info_rejects_injection_shaped_table_names(tmp_path):
    db = DatabaseManager(_seed_database(tmp_path), read_only=True)

    assert db.get_table_info("users; DROP TABLE users") == []
    # The guard must not have let anything through to the database.
    assert [column["name"] for column in db.get_table_info("users")] == ["id", "name", "note"]


def test_list_tables_hides_sqlite_internal_bookkeeping(tmp_path):
    db_path = tmp_path / "internals.sqlite"
    db_path.touch()
    manager = DatabaseManager(str(db_path), read_only=False)
    # AUTOINCREMENT makes SQLite create its own sqlite_sequence table.
    ok, _ = manager.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT)")
    assert ok is True
    ok, _ = manager.execute("CREATE TABLE people (id INTEGER PRIMARY KEY)")
    assert ok is True

    ok, raw = manager.execute("SELECT name FROM sqlite_master WHERE type='table'")
    assert ok is True
    # Guard against a vacuous test: the internal table must really be there.
    assert "sqlite_sequence" in {row[0] for row in raw["rows"]}

    assert manager.list_tables() == ["notes", "people"]
