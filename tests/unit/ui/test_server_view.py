from pathlib import Path

from fesium.ui.views.server_view import build_server_view_model, resolve_server_action_layout


def test_build_server_view_model_exposes_button_guards():
    model = build_server_view_model(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        document_root=Path("C:/Projects/demo"),
        port=8000,
        backend_kind="static",
        server_status="stopped",
        local_url="",
        last_error="",
    )

    assert model["status_label"] == "Stopped"
    assert model["backend_label"] == "Static Fallback"
    assert model["port_label"] == "8000"
    assert model["actions"]["start"] is True
    assert model["actions"]["stop"] is False
    assert model["actions"]["restart"] is False
    assert model["actions"]["open_in_browser"] is False


def test_resolve_server_action_layout_keeps_single_row_on_wide_width():
    layout = resolve_server_action_layout(available_width=1200)
    assert layout == [["select_project", "start", "stop", "restart", "open_in_browser"]]


def test_resolve_server_action_layout_wraps_to_two_rows_when_narrow():
    layout = resolve_server_action_layout(available_width=760)
    assert layout == [["select_project", "start", "stop"], ["restart", "open_in_browser"]]


def test_build_server_view_model_keeps_log_text():
    model = build_server_view_model(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        document_root=Path("C:/Projects/demo"),
        port=8000,
        backend_kind="static",
        server_status="running",
        local_url="http://localhost:8000",
        last_error="",
        log_lines=("Line 1", "Line 2"),
    )

    assert model["log_text"] == "Line 1\nLine 2"
