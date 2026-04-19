from pathlib import Path

from fesium.ui.views.server_view import build_server_view_model


def test_build_server_view_model_exposes_button_guards():
    model = build_server_view_model(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        document_root=Path("C:/Projects/demo"),
        backend_kind="static",
        server_status="stopped",
        local_url="",
        last_error="",
    )

    assert model["status_label"] == "Stopped"
    assert model["backend_label"] == "Static Fallback"
    assert model["actions"]["start"] is True
    assert model["actions"]["stop"] is False
    assert model["actions"]["restart"] is False
    assert model["actions"]["open_in_browser"] is False
