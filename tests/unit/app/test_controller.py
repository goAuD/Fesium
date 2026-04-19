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


def test_start_moves_controller_to_running_and_stores_local_url(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path,
        project_kind="standard",
        document_root=tmp_path,
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
