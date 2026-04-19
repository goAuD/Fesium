from fesium.ui.views.database_view import (
    build_database_result_view_model,
    build_database_summary,
)


def test_build_database_summary_surfaces_read_only_badge():
    summary = build_database_summary(
        "D:/site/database.sqlite",
        True,
        source="project",
        project_database_available=False,
    )

    assert summary["mode_badge"] == "Read-only Enabled"


def test_build_database_summary_surfaces_manual_source_and_write_mode():
    summary = build_database_summary(
        db_path="D:/db/demo.sqlite",
        read_only=False,
        source="manual",
        project_database_available=True,
    )

    assert summary["source_badge"] == "Manual Database"
    assert summary["mode_badge"] == "Write Mode"
    assert summary["can_reset"] is True


def test_build_database_result_view_model_handles_read_results():
    model = build_database_result_view_model(
        {"kind": "read", "columns": ["name"], "rows": [("Ada",)], "count": 1},
        "",
    )

    assert model["title"] == "1 row"
    assert "Ada" in model["body"]


def test_build_database_result_view_model_prefers_explicit_error():
    model = build_database_result_view_model(
        {"kind": "none"},
        "Read-only mode: Write operations are disabled",
    )

    assert model["tone"] == "accent.danger"
