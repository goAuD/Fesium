from fesium.ui.views.database_view import (
    build_database_result_view_model,
    build_database_summary,
    format_query_result_table,
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
        {"kind": "read", "columns": ["id", "name"], "rows": [(1, "Ada")], "count": 1},
        "",
    )

    assert model["title"] == "1 row"
    assert "id | name" in model["body"]
    assert "1  | Ada " in model["body"]


def test_build_database_result_view_model_prefers_explicit_error():
    model = build_database_result_view_model(
        {"kind": "none"},
        "Read-only mode: Write operations are disabled",
    )

    assert model["tone"] == "accent.danger"


def test_format_query_result_table_aligns_variable_width_columns():
    table = format_query_result_table(
        ["id", "name"],
        [(1, "Test User"), (22, "Alice"), (333, "Bob")],
    )

    lines = table.splitlines()
    assert lines[0] == "id  | name     "
    assert lines[1] == "----+----------"
    assert lines[2] == "1   | Test User"
    assert lines[3] == "22  | Alice    "
    assert lines[4] == "333 | Bob      "
