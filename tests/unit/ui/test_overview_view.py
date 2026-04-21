from pathlib import Path

from fesium.ui.views.overview_view import build_overview_cards


def test_build_overview_cards_surfaces_workspace_and_health():
    cards = build_overview_cards(
        project_root=Path("D:/site"),
        project_kind="standard",
        php_summary="PHP 8.4.0",
        server_status="running",
        local_url="http://localhost:8000",
        log_lines=("Selected project: D:/site", "[Fesium] Started at http://localhost:8000"),
    )

    assert cards[0]["title"] == "Workspace"
    assert cards[0]["value"] == str(Path("D:/site"))
    assert cards[1]["badge"] == "Running"
    assert "http://localhost:8000" in cards[1]["value"]
    assert cards[3]["title"] == "Recent Activity"
    assert "Started" in cards[3]["value"]
