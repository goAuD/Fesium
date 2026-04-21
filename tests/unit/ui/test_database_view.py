from fesium.ui.views.database_view import (
    build_database_result_view_model,
    build_database_schema_view_model,
    build_database_summary,
    format_schema_table,
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
    assert "Columns: 2" in model["body"]


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


def test_build_database_schema_view_model_selects_first_table_by_default():
    model = build_database_schema_view_model(
        tables=("posts", "users"),
        selected_table="",
        selected_table_info=(
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
        ),
    )

    assert model["selected_table"] == "posts"
    assert model["tables"][0]["active"] is True


def test_format_schema_table_renders_column_metadata():
    body = format_schema_table(
        (
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            {"name": "email", "type": "TEXT", "nullable": True, "primary_key": False},
        )
    )

    assert "name  | type" in body
    assert "id" in body
    assert "email" in body
