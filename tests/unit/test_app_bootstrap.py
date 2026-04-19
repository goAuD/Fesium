from pathlib import Path
from types import SimpleNamespace

from fesium.app import build_app_context, build_default_paths, main
from fesium.app.bootstrap import _replace_runtime_views


def test_fesium_app_package_exports_bootstrap_symbols():
    assert callable(build_app_context)
    assert callable(build_default_paths)
    assert callable(main)


def test_build_app_context_uses_last_project_or_cwd(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": ""},
    )

    assert context.project_root == tmp_path
    assert context.active_view == "overview"


def test_build_app_context_preserves_last_project(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": str(tmp_path / "demo"), "active_view": "server"},
    )

    assert context.project_root == (tmp_path / "demo").resolve()
    assert context.active_view == "server"


def test_replace_runtime_views_rebuilds_database_view_for_current_project(
    tmp_path, monkeypatch
):
    startup_project = (tmp_path / "startup").resolve()
    current_project = (tmp_path / "current").resolve()

    state = SimpleNamespace(
        project_root=current_project,
        project_kind="standard",
        document_root=current_project,
        backend_kind="static",
        server_status="stopped",
        local_url="",
        php_summary="PHP not found in PATH",
        last_error="",
        log_lines=(),
    )
    controller = SimpleNamespace(state=state)

    class FakeShell:
        def __init__(self):
            self.factories = {}

        def replace_view(self, view_id, factory):
            self.factories[view_id] = factory

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            self.db_path = db_path
            self.read_only = read_only

    monkeypatch.setattr(
        "fesium.app.bootstrap.detect_project_profile",
        lambda root: SimpleNamespace(database_path=Path(root) / "database.sqlite"),
    )
    monkeypatch.setattr("fesium.app.bootstrap.DatabaseManager", FakeDatabaseManager)
    monkeypatch.setattr(
        "fesium.app.bootstrap.DatabaseView",
        lambda parent, db_path, read_only: {"db_path": db_path, "read_only": read_only},
    )
    monkeypatch.setattr("fesium.app.bootstrap.OverviewView", lambda *args, **kwargs: None)
    monkeypatch.setattr("fesium.app.bootstrap.ServerView", lambda *args, **kwargs: None)

    shell = FakeShell()
    config = SimpleNamespace(port=8000)

    _replace_runtime_views(
        shell=shell,
        controller=controller,
        config=config,
        fallback_project=startup_project,
        select_project_action=lambda: None,
        start_action=lambda: None,
        stop_action=lambda: None,
        restart_action=lambda: None,
        open_browser_action=lambda: None,
    )

    database_view = shell.factories["database"](None)

    assert database_view["db_path"] == str(current_project / "database.sqlite")
    assert database_view["read_only"] is True
