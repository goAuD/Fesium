from fesium.core.environment import EnvironmentStatus
from fesium.ui.views.environment_view import build_environment_rows


def test_build_environment_rows_contains_php_summary():
    rows = build_environment_rows(
        EnvironmentStatus(True, "PHP 8.4.0", "PHP 8.4.0"),
        project_root="D:/site",
        project_kind="standard",
        document_root="D:/site/public",
    )

    assert rows[0]["label"] == "PHP"
    assert any(row["label"] == "Validation" for row in rows)
