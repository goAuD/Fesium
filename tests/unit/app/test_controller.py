from pathlib import Path

from fesium.app.controller import FesiumController
from fesium.core.environment import EnvironmentStatus
from fesium.core.project_detection import ProjectProfile
from fesium.core.runtime_detection import RuntimeDecision


def test_controller_starts_with_stopped_state(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    state = controller.state

    assert state.server_status == "stopped"
    assert state.backend_kind == "none"
    assert state.php_summary == ""
    assert state.log_lines == ()


def test_controller_starts_with_database_read_only_enabled(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert controller.state.database_path is None
    assert controller.state.database_source == "none"
    assert controller.state.database_read_only is True
    assert controller.state.database_last_query == ""
    assert controller.state.database_last_result == {"kind": "none"}
    assert controller.state.database_last_error == ""


def test_controller_log_buffer_is_bounded(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path, log_limit=3)

    controller.append_log("one")
    controller.append_log("two")
    controller.append_log("three")
    controller.append_log("four")

    assert controller.state.log_lines == ("two", "three", "four")


def test_controller_rejects_nonpositive_log_limit(tmp_path):
    for log_limit in (0, -1):
        try:
            FesiumController(config=None, cwd=tmp_path, log_limit=log_limit)
        except ValueError as exc:
            assert "log_limit" in str(exc)
        else:
            raise AssertionError("expected ValueError for nonpositive log_limit")


def test_controller_select_project_updates_state_and_persists_last_project(
    tmp_path, monkeypatch
):
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()

    calls = []

    class FakeConfig:
        def set(self, key, value):
            calls.append((key, value))

    controller = FesiumController(config=FakeConfig(), cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=Path("C:/old-project"),
        project_kind="legacy",
        document_root=Path("C:/old-project/public"),
        database_path=None,
        database_source="none",
        database_read_only=False,
        database_last_query="SELECT * FROM legacy",
        database_last_result={"kind": "read", "columns": ["id"], "rows": [(1,)], "count": 1},
        database_last_error="db boom",
        backend_kind="php",
        server_status="running",
        local_url="http://localhost:8000",
        php_available=True,
        php_summary="PHP 8.3.0",
        last_error="boom",
        log_lines=("previous log",),
    )

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: ProjectProfile(
            root=Path(path).resolve(),
            kind="standard",
            document_root=Path(path).resolve() / "public",
            database_path=None,
        ),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: EnvironmentStatus(php_available=True, php_version="8.3.0", summary="PHP 8.3.0"),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(
            backend_kind="php",
            reason=f"php_available_for_{profile.kind}" if php_available else "php_unavailable",
        ),
    )

    controller.select_project(project_dir)

    state = controller.state
    assert state.project_root == project_dir.resolve()
    assert state.project_kind == "standard"
    assert state.document_root == project_dir.resolve() / "public"
    assert state.database_path is None
    assert state.database_source == "none"
    assert state.database_read_only is True
    assert state.database_last_query == ""
    assert state.database_last_result == {"kind": "none"}
    assert state.database_last_error == ""
    assert state.backend_kind == "php"
    assert state.server_status == "stopped"
    assert state.local_url == ""
    assert state.php_available is True
    assert state.php_summary == "PHP 8.3.0"
    assert state.last_error == ""
    assert state.log_lines == (
        "previous log",
        f"Selected project: {project_dir.resolve()}",
        "Backend selected: php",
    )
    assert calls == [("last_project", str(project_dir.resolve()))]


def test_select_project_stops_running_backend_before_resetting_state(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()
    stopped = []

    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path / "old-project",
        project_kind="standard",
        document_root=tmp_path / "old-project",
        database_path=None,
        database_source="none",
        database_read_only=False,
        database_last_query="DELETE FROM users",
        database_last_result={"kind": "error", "message": "blocked"},
        database_last_error="blocked",
        backend_kind="static",
        server_status="running",
        local_url="http://localhost:8000",
        php_available=False,
        php_summary="PHP not found",
        last_error="",
        log_lines=(),
    )

    class FakeBackend:
        def stop(self):
            stopped.append("stopped")

    controller._backend = FakeBackend()

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: ProjectProfile(
            root=Path(path).resolve(),
            kind="standard",
            document_root=Path(path).resolve() / "public",
            database_path=None,
        ),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: EnvironmentStatus(php_available=False, php_version="", summary="PHP not found"),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(
            backend_kind="static",
            reason="php_unavailable",
        ),
    )

    controller.select_project(project_dir)

    assert stopped == ["stopped"]
    assert controller._backend is None
    assert controller.state.server_status == "stopped"
    assert controller.state.local_url == ""


def test_select_project_rejects_missing_directory_without_stopping_running_backend(tmp_path):
    missing = tmp_path / "missing-project"
    stopped = []
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path / "old-project",
        project_kind="standard",
        document_root=tmp_path / "old-project",
        database_path=None,
        database_source="none",
        database_read_only=True,
        database_last_query="",
        database_last_result={"kind": "none"},
        database_last_error="",
        backend_kind="static",
        server_status="running",
        local_url="http://localhost:8000",
        php_available=False,
        php_summary="PHP not found",
        last_error="",
        log_lines=(),
    )

    class FakeBackend:
        def stop(self):
            stopped.append("stopped")

    controller._backend = FakeBackend()

    assert controller.select_project(missing) is False
    assert stopped == []
    assert controller.state.server_status == "running"
    assert "does not exist" in controller.state.last_error


def test_start_moves_controller_to_running_and_stores_local_url(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path,
        project_kind="standard",
        document_root=tmp_path,
        database_path=None,
        database_source="none",
        database_read_only=True,
        database_last_query="",
        database_last_result={"kind": "none"},
        database_last_error="",
        backend_kind="static",
        server_status="stopped",
        local_url="",
        php_available=False,
        php_summary="PHP not found",
        last_error="previous error",
        log_lines=(),
    )

    class FakeBackend:
        is_running = False

        def start(self, document_root, port):
            assert document_root == tmp_path
            assert port == 8000
            self.is_running = True
            return "http://localhost:8000"

        def stop(self):
            self.is_running = False

    controller._backend = FakeBackend()

    assert controller.start() is True
    assert controller.state.server_status == "running"
    assert controller.state.local_url == "http://localhost:8000"
    assert controller.state.last_error == ""


def test_start_converts_backend_exceptions_into_error_state(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path,
        project_kind="standard",
        document_root=tmp_path,
        database_path=None,
        database_source="none",
        database_read_only=True,
        database_last_query="",
        database_last_result={"kind": "none"},
        database_last_error="",
        backend_kind="static",
        server_status="stopped",
        local_url="",
        php_available=False,
        php_summary="PHP not found",
        last_error="",
        log_lines=(),
    )

    class FakeBackend:
        def start(self, document_root, port):
            raise OSError("Port 8000 is already in use")

    controller._backend = FakeBackend()

    assert controller.start() is False
    assert controller.state.server_status == "error"
    assert controller.state.last_error == "Port 8000 is already in use"
    assert controller.state.log_lines[-1] == "[Fesium] ERROR: Port 8000 is already in use"


def test_start_rejects_missing_document_root_with_specific_error(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    missing_root = tmp_path / "missing"
    controller.state = controller.state.__class__(
        project_root=tmp_path,
        project_kind="standard",
        document_root=missing_root,
        database_path=None,
        database_source="none",
        database_read_only=True,
        database_last_query="",
        database_last_result={"kind": "none"},
        database_last_error="",
        backend_kind="static",
        server_status="stopped",
        local_url="",
        php_available=False,
        php_summary="PHP not found",
        last_error="",
        log_lines=(),
    )

    assert controller.start() is False
    assert controller.state.server_status == "error"
    assert str(missing_root.resolve()) in controller.state.last_error


def test_restart_is_rejected_while_stopped(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert controller.restart() is False
    assert controller.state.server_status == "stopped"
    assert controller.state.log_lines[-1] == "[Fesium] Restart rejected: server not running"


def test_open_in_browser_is_rejected_without_running_server(tmp_path, monkeypatch):
    controller = FesiumController(config=None, cwd=tmp_path)
    opened = []
    monkeypatch.setattr("fesium.app.controller.open_local_url", lambda url: opened.append(url))

    assert controller.open_in_browser() is False
    assert opened == []
    assert controller.state.log_lines[-1] == "[Fesium] Open in Browser rejected: server not running"


def test_select_project_populates_project_database_when_detected(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()
    database_path = project_dir / "database.sqlite"
    database_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: ProjectProfile(
            root=project_dir.resolve(),
            kind="standard",
            document_root=project_dir.resolve(),
            database_path=database_path.resolve(),
        ),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: EnvironmentStatus(php_available=False, php_version="", summary="PHP not found"),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(backend_kind="static", reason="php_unavailable"),
    )

    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_project(project_dir)

    assert controller.state.database_path == database_path.resolve()
    assert controller.state.database_source == "project"
    assert controller.state.database_read_only is True


def test_select_database_marks_manual_source_and_preserves_choice(tmp_path):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)

    controller.select_database(db_file)

    assert controller.state.database_path == db_file.resolve()
    assert controller.state.database_source == "manual"


def test_select_database_populates_schema_browser_state(tmp_path, monkeypatch):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            assert db_path == str(db_file.resolve())
            assert read_only is True

        def list_tables(self):
            return ["posts", "users"]

        def get_table_info(self, table_name):
            return [{"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True}]

    monkeypatch.setattr("fesium.app.controller.DatabaseManager", FakeDatabaseManager)

    controller.select_database(db_file)

    assert controller.state.database_tables == ("posts", "users")
    assert controller.state.database_selected_table == "posts"
    assert controller.state.database_selected_table_info[0]["name"] == "id"


def test_manual_database_choice_survives_project_refresh(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()
    project_db = project_dir / "database.sqlite"
    project_db.write_text("", encoding="utf-8")
    manual_db = tmp_path / "manual.sqlite"
    manual_db.write_text("", encoding="utf-8")

    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_database(manual_db)
    controller.set_database_read_only(False)

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: ProjectProfile(
            root=project_dir.resolve(),
            kind="standard",
            document_root=project_dir.resolve(),
            database_path=project_db.resolve(),
        ),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: EnvironmentStatus(php_available=False, php_version="", summary="PHP not found"),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(backend_kind="static", reason="php_unavailable"),
    )

    controller.select_project(project_dir)

    assert controller.state.database_path == manual_db.resolve()
    assert controller.state.database_source == "manual"
    assert controller.state.database_read_only is True


def test_select_database_table_switches_schema_focus(tmp_path, monkeypatch):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            pass

        def list_tables(self):
            return ["posts", "users"]

        def get_table_info(self, table_name):
            return [{"name": f"{table_name}_id", "type": "INTEGER", "nullable": False, "primary_key": True}]

    monkeypatch.setattr("fesium.app.controller.DatabaseManager", FakeDatabaseManager)

    controller.select_database(db_file)
    assert controller.select_database_table("users") is True

    assert controller.state.database_selected_table == "users"
    assert controller.state.database_selected_table_info[0]["name"] == "users_id"


def test_reset_to_project_database_restores_detected_database(tmp_path):
    project_db = tmp_path / "project.sqlite"
    project_db.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller._project_database_path = project_db.resolve()
    controller.state = controller.state.__class__(
        **{**controller.state.__dict__, "database_path": None, "database_source": "none"}
    )

    assert controller.reset_to_project_database() is True
    assert controller.state.database_path == project_db.resolve()
    assert controller.state.database_source == "project"


def test_run_database_query_blocks_write_query_in_read_only_mode(tmp_path):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_database(db_file)

    ok = controller.run_database_query("DELETE FROM users")

    assert ok is False
    assert controller.state.database_last_result["kind"] == "error"
    assert "Read-only mode" in controller.state.database_last_error


def test_run_database_query_stores_read_result(tmp_path, monkeypatch):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_database(db_file)

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            assert db_path == str(db_file.resolve())
            assert read_only is True

        def execute(self, query, params=()):
            return True, {"columns": ["name"], "rows": [("Ada",)], "count": 1}

    monkeypatch.setattr("fesium.app.controller.DatabaseManager", FakeDatabaseManager)

    ok = controller.run_database_query("SELECT name FROM users")

    assert ok is True
    assert controller.state.database_last_result["kind"] == "read"
    assert controller.state.database_last_result["count"] == 1
    assert controller.state.database_last_error == ""


def test_preview_database_table_runs_select_star_limit_query(tmp_path, monkeypatch):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        **{
            **controller.state.__dict__,
            "database_path": db_file.resolve(),
            "database_source": "manual",
            "database_tables": ("users",),
            "database_selected_table": "users",
            "database_selected_table_info": (
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            ),
        }
    )

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            assert db_path == str(db_file.resolve())

        def execute(self, query, params=()):
            assert query == "SELECT * FROM users LIMIT 100"
            return True, {"columns": ["id"], "rows": [(1,)], "count": 1}

        def list_tables(self):
            return ["users"]

        def get_table_info(self, table_name):
            return [{"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True}]

    monkeypatch.setattr("fesium.app.controller.DatabaseManager", FakeDatabaseManager)

    assert controller.preview_database_table() is True
    assert controller.state.database_last_query == "SELECT * FROM users LIMIT 100"
    assert controller.state.database_last_result["kind"] == "read"
