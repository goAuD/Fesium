from fesium.core.environment import EnvironmentStatus
from fesium.ui.views.environment_view import build_environment_rows


def test_build_environment_rows_contains_php_summary():
    rows = build_environment_rows(EnvironmentStatus(True, "PHP 8.4.0", "PHP 8.4.0"))

    assert rows[0]["label"] == "PHP"
