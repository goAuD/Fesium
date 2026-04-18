from pathlib import Path

from fesium.ui.views.server_view import build_server_status


def test_build_server_status_reports_running_state():
    status = build_server_status(Path("D:/site/public"), 8000, True)

    assert status["label"] == "Running"
    assert status["url"] == "http://localhost:8000"
