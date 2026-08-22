from pathlib import Path

from fesium.ui.views.overview_view import build_overview_cards, build_overview_model


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


def test_a_static_project_reports_the_static_server_not_a_php_version():
    """Showing a PHP version for a site that never touches PHP reads as though
    PHP were part of the project."""
    model = build_overview_model(
        project_root=Path("D:/GitHub/CoderQuiz"),
        project_kind="standard",
        php_summary="PHP 8.5.2 (cli)",
        server_status="running",
        local_url="http://localhost:8000",
        needs_php=False,
    )

    assert "PHP" not in model["runtime_summary"]
    assert "Static server" in model["runtime_summary"]
    assert model["runtime_meta"] == "no runtime needed"
    assert model["runtime_tone"] == "accent.success"


def test_a_php_project_still_reports_the_php_version():
    model = build_overview_model(
        project_root=Path("D:/GitHub/streamapp"),
        project_kind="laravel",
        php_summary="PHP 8.5.2 (cli)",
        server_status="running",
        local_url="http://localhost:8000",
        needs_php=True,
    )

    assert model["runtime_summary"] == "PHP 8.5.2 (cli)"
    assert model["runtime_meta"] == "healthy"


def test_a_php_project_without_php_is_flagged():
    model = build_overview_model(
        project_root=Path("D:/GitHub/streamapp"),
        project_kind="laravel",
        php_summary="",
        server_status="stopped",
        local_url="",
        needs_php=True,
    )

    assert model["runtime_meta"] == "missing"
    assert model["runtime_tone"] == "accent.danger"
