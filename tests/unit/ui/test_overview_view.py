from pathlib import Path

from fesium.core.project_detection import ProjectProfile
from fesium.ui.views.overview_view import build_overview_cards


def test_build_overview_cards_surfaces_workspace_and_health():
    profile = ProjectProfile(Path("D:/site"), "standard", Path("D:/site"), None)

    cards = build_overview_cards(
        profile,
        php_summary="PHP 8.4.0",
        server_running=False,
    )

    assert "Workspace" in cards[0]["title"]
    assert any(card["title"] == "Environment Health" for card in cards)
