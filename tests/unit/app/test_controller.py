from pathlib import Path

from fesium.app.controller import FesiumController


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

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: type(
            "Profile",
            (),
            {
                "root": Path(path).resolve(),
                "kind": "standard",
                "document_root": Path(path).resolve() / "public",
            },
        )(),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: type("EnvironmentStatus", (), {"php_available": True})(),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: type(
            "RuntimeDecision",
            (),
            {"backend_kind": "php"},
        )(),
    )

    controller.select_project(project_dir)

    state = controller.state
    assert state.project_root == project_dir.resolve()
    assert state.project_kind == "standard"
    assert state.document_root == project_dir.resolve() / "public"
    assert state.backend_kind == "php"
    assert state.php_available is True
    assert state.log_lines == (
        f"Selected project: {project_dir.resolve()}",
        "Backend selected: php",
    )
    assert calls == [("last_project", str(project_dir.resolve()))]
