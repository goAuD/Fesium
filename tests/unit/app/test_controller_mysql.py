"""MySQL session tests for the controller.

The password guardrail is pinned here: it lives on one private controller
attribute, never on ControllerState, never in its repr, never on disk. All
engines and probes are fakes - no test opens a socket.
"""

import dataclasses

from fesium.app.controller import ControllerState, FesiumController
from fesium.core.database_engines import MYSQL_READ_VERBS
from fesium.core.project_database import ConnectionSettings

SETTINGS = ConnectionSettings(engine="mysql", host="db.local", port=3306, database="shop", user="root")
PASSWORD = "session-only-secret"


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

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class FakeConnection:
    def __init__(self, rows=(), description=None):
        self.executed = []
        self.rows = list(rows)
        self.description = description

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class FakeMySQLEngine:
    """Stands in for MySQLEngine without touching pymysql at all."""

    placeholder = "%s"
    read_verbs = MYSQL_READ_VERBS
    errors = (ConnectionError,)

    def __init__(self, connection=None, connect_error=None):
        self.connection = connection if connection is not None else FakeConnection()
        self.connect_error = connect_error
        self.connect_kwargs = None

    def connect(self, target, *, read_only):
        self.connect_kwargs = {"target": target, "read_only": read_only}
        if self.connect_error is not None:
            raise self.connect_error
        return self.connection

    def availability_error(self, target):
        return None

    def list_tables_query(self):
        return ("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()", ())

    def table_columns_query(self, table_name):
        return (
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
            (table_name,),
        )

    def interpret_column_rows(self, rows):
        return [{"name": row[0], "type": "", "nullable": True, "primary_key": False} for row in rows]


def connect(controller, tmp_path=None, *, engine=None, probe_result=True):
    """Run connect_mysql fully stubbed so nothing touches a socket."""
    import fesium.app.controller as controller_module

    original_probe = controller_module.probe_database
    controller_module.probe_database = lambda requirement: probe_result
    try:
        # Default to the fake engine so a forgotten injection can never
        # turn into a real connection attempt.
        return controller.connect_mysql(SETTINGS, PASSWORD, engine=engine or FakeMySQLEngine())
    finally:
        controller_module.probe_database = original_probe


def test_connect_mysql_success_sets_state_and_keeps_session_password(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert connect(controller) is True

    assert controller.state.database_connected is True
    assert controller.state.database_engine == "mysql"
    assert controller.state.database_connection_settings == SETTINGS
    # The password lives on the private session attribute - and nowhere else.
    assert controller._database_password == PASSWORD


def test_password_never_enters_any_state_field_or_repr(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    connect(controller)

    state = controller.state
    for field in dataclasses.fields(ControllerState):
        value = getattr(state, field.name)
        assert PASSWORD not in repr(value), f"password leaked into field {field.name}"

    assert PASSWORD not in repr(state)
    assert PASSWORD not in str(state)
    assert PASSWORD not in repr(controller)


def test_connect_mysql_reports_dead_host_plainly_with_address(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert connect(controller, probe_result=False) is False

    message = controller.state.database_last_error
    assert "Nothing is listening at db.local:3306" in message
    # Plain words, no stack trace.
    assert "Traceback" not in message
    assert controller.state.database_connected is False
    assert controller._database_password is None


def test_connect_mysql_reports_refused_connection_plainly(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    engine = FakeMySQLEngine(connect_error=ConnectionError("(2003) Can't connect to server"))

    assert connect(controller, engine=engine) is False

    message = controller.state.database_last_error
    assert "db.local:3306" in message
    assert "refused" in message
    assert "Traceback" not in message
    assert controller._database_password is None
    assert controller._mysql_manager is None


def test_disconnect_mysql_clears_session_and_forgets_password(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    connect(controller)

    assert controller.disconnect_mysql() is True

    assert controller.state.database_connected is False
    assert controller.state.database_connection_settings is None
    assert controller._database_password is None
    assert controller._mysql_manager is None


def test_queries_route_through_the_mysql_session(tmp_path):
    connection = FakeConnection(rows=[("users",)], description=[("table_name",)])
    engine = FakeMySQLEngine(connection=connection)
    controller = FesiumController(config=None, cwd=tmp_path)
    connect(controller, engine=engine)

    assert controller.run_database_query("SHOW TABLES") is True

    result = controller.state.database_last_result
    assert result["kind"] == "read"
    assert result["columns"] == ["table_name"]
    assert result["rows"] == [("users",)]


def test_write_is_blocked_in_read_only_mysql_session_before_the_wire(tmp_path):
    connection = FakeConnection()
    engine = FakeMySQLEngine(connection=connection)
    controller = FesiumController(config=None, cwd=tmp_path)
    connect(controller, engine=engine)
    statements_before = len(connection.executed)

    assert controller.run_database_query("UPDATE users SET name = 'x'") is False

    assert "Read-only mode" in controller.state.database_last_error
    # Blocked at the gate - nothing new reached the fake connection.
    assert len(connection.executed) == statements_before


def test_toggling_read_only_drops_the_mysql_session(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    connect(controller)

    controller.set_database_read_only(False)

    assert controller.state.database_connected is False
    assert controller._database_password is None
