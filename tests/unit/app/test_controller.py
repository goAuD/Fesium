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
    assert state.last_error == ""
    assert state.log_lines == (
        "previous log",
        f"Selected project: {project_dir.resolve()}",
        "Backend selected: php",
    )
    assert calls == [("last_project", str(project_dir.resolve()))]
