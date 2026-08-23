"""MySQL engine seam tests.

None of these tests open a network connection. ``MySQLEngine`` takes its
connector as an injectable argument precisely so this suite can hand in a
fake instead of a socket.
"""

import ast
from pathlib import Path

from fesium.core.database import DatabaseManager
from fesium.core.database_engines import (
    MYSQL_CONNECT_TIMEOUT_SECONDS,
    MYSQL_READ_VERBS,
    MySQLEngine,
    query_is_read,
)


class FakeCursor:
    def __init__(self, owner):
        self._owner = owner

    def execute(self, query, params=None):
        self._owner.executed.append((query, params))

    def fetchall(self):
        return self._owner.rows

    @property
    def description(self):
        return self._owner.description

    @property
    def rowcount(self):
        return self._owner.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class FakeConnection:
    def __init__(self, rows=(), description=None, rowcount=-1):
        self.executed = []
        self.rows = list(rows)
        self.description = description
        self.rowcount = rowcount
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True


class RecordingConnector:
    """Stands in for pymysql.connect and records what it was asked to do."""

    def __init__(self):
        self.calls = []
        self.connection = FakeConnection()

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.connection


def make_mysql_engine(connection=None):
    connector = RecordingConnector()
    if connection is not None:
        connector.connection = connection
    engine = MySQLEngine(
        host="db.example.local",
        port=3307,
        user="student",
        password="not-a-real-secret",
        connector=connector,
    )
    return engine, connector


def test_mysql_engine_lists_tables_through_information_schema():
    engine, _ = make_mysql_engine()

    sql, params = engine.list_tables_query()

    assert "information_schema.tables" in sql
    assert "DATABASE()" in sql
    # Nothing is interpolated: the schema comes from DATABASE(), so the
    # parameter list is empty.
    assert params == ()
    assert engine.placeholder == "%s"


def test_mysql_engine_binds_the_table_name_in_the_columns_query():
    engine, _ = make_mysql_engine()

    sql, params = engine.table_columns_query("users")

    assert "information_schema.columns" in sql
    assert params == ("users",)
    # The name travels as a bound parameter, never formatted into the string.
    assert "users" not in sql


def test_mysql_engine_maps_information_schema_rows_to_shared_shape():
    engine, _ = make_mysql_engine()

    columns = engine.interpret_column_rows(
        [
            ("id", "int(11)", "NO", "PRI"),
            ("name", "varchar(255)", "YES", ""),
            ("note", "text", "YES", "MUL"),
        ]
    )

    assert columns[0] == {"name": "id", "type": "int(11)", "nullable": False, "primary_key": True}
    assert columns[1] == {"name": "name", "type": "varchar(255)", "nullable": True, "primary_key": False}
    # MUL keys are indexes, not primary keys.
    assert columns[2]["primary_key"] is False


def test_mysql_read_verbs_cover_the_dialect_and_reject_writes():
    assert query_is_read("SELECT * FROM users", MYSQL_READ_VERBS) is True
    assert query_is_read("SHOW TABLES", MYSQL_READ_VERBS) is True
    assert query_is_read("DESCRIBE users", MYSQL_READ_VERBS) is True
    assert query_is_read("DESC users", MYSQL_READ_VERBS) is True
    assert query_is_read("EXPLAIN SELECT * FROM users", MYSQL_READ_VERBS) is True

    assert query_is_read("UPDATE users SET id = 1", MYSQL_READ_VERBS) is False
    assert query_is_read("CALL do_thing()", MYSQL_READ_VERBS) is False
    assert query_is_read("GRANT ALL ON *.* TO 'x'@'y'", MYSQL_READ_VERBS) is False
    assert query_is_read("TRUNCATE users", MYSQL_READ_VERBS) is False


def test_mysql_engine_connects_with_bounded_timeout_and_read_only_session():
    engine, connector = make_mysql_engine()

    engine.connect("shop", read_only=True)

    kwargs = connector.calls[0]
    assert kwargs["host"] == "db.example.local"
    assert kwargs["port"] == 3307
    assert kwargs["user"] == "student"
    assert kwargs["database"] == "shop"
    # A dead host must not freeze the UI: the timeout has to travel with the
    # connect call itself.
    assert kwargs["connect_timeout"] == MYSQL_CONNECT_TIMEOUT_SECONDS
    assert kwargs["connect_timeout"] > 0
    # Read-only twice over: the session is pinned read-only on connect.
    assert connector.connection.executed[0] == ("SET SESSION TRANSACTION READ ONLY", None)


def test_mysql_engine_skips_session_pin_when_not_read_only():
    engine, connector = make_mysql_engine()

    engine.connect("shop", read_only=False)

    assert connector.connection.executed == []


def test_database_manager_runs_reads_through_mysql_engine():
    connection = FakeConnection(
        rows=[("users",), ("orders",)],
        description=[("table_name",)],
    )
    engine, connector = make_mysql_engine(connection)
    manager = DatabaseManager("shop", read_only=True, engine=engine)

    ok, result = manager.execute("SHOW TABLES")

    assert ok is True
    assert result == {"columns": ["table_name"], "rows": [("users",), ("orders",)], "count": 2}
    # The SET SESSION pin ran before the user query, inside the same session.
    assert [query for query, _ in connector.connection.executed] == [
        "SET SESSION TRANSACTION READ ONLY",
        "SHOW TABLES",
    ]


def test_database_manager_blocks_writes_on_mysql_before_touching_the_wire():
    engine, connector = make_mysql_engine()
    manager = DatabaseManager("shop", read_only=True, engine=engine)

    ok, message = manager.execute("UPDATE users SET name = 'x'")

    assert ok is False
    assert "Read-only mode" in message
    # Blocked at the gate: no connection was even attempted.
    assert connector.calls == []


def test_database_manager_reports_connection_failure_from_mysql_engine():
    class FailingConnector:
        def __call__(self, **kwargs):
            import pymysql

            raise pymysql.err.OperationalError(
                2003, f"Can't connect to MySQL server on '{kwargs['host']}'"
            )

    engine = MySQLEngine(
        host="dead.host.local", port=3306, user="root", password="x", connector=FailingConnector()
    )
    manager = DatabaseManager("shop", read_only=True, engine=engine)

    ok, message = manager.execute("SHOW TABLES")

    assert ok is False
    assert "dead.host.local" in message


def test_mysql_engine_error_type_is_the_driver_error():
    import pymysql

    engine, _ = make_mysql_engine()

    assert engine.errors == (pymysql.MySQLError,)


def test_pymysql_is_never_imported_at_module_level():
    import fesium.core.database_engines as module

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))

    module_level_ids = {id(node) for node in tree.body}
    module_level_names = set()
    function_level_pymysql_imports = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
        roots = {name.split(".")[0] for name in names}
        if id(node) in module_level_ids:
            module_level_names.update(roots)
        elif isinstance(node, ast.Import) and "pymysql" in roots:
            function_level_pymysql_imports += 1

    assert "pymysql" not in module_level_names
    # It is imported somewhere - strictly inside functions, twice (connect
    # and the errors property).
    assert function_level_pymysql_imports >= 2

