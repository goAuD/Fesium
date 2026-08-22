from pathlib import Path

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


def _status(available=True, version="PHP 8.5.2 (cli)", path="C:/php/php.EXE"):
    return EnvironmentStatus(available, version if available else "", version if available else "missing", path)


def _row(rows, label):
    return next(row["value"] for row in rows if row["label"] == label)


def test_diagnostics_names_the_binary_it_probed():
    """A machine can carry several PHP installs; the version alone does not
    say which one PATH resolved to."""
    rows = build_environment_rows(
        _status(), project_root=Path("D:/GitHub/streamapp"), project_kind="laravel",
        document_root=Path("D:/GitHub/streamapp/public"), needs_php=True,
    )

    assert _row(rows, "Binary") == "C:/php/php.EXE"


def test_diagnostics_says_php_is_not_used_by_a_static_project():
    rows = build_environment_rows(
        _status(), project_root=Path("D:/GitHub/CoderQuiz"), project_kind="standard",
        document_root=Path("D:/GitHub/CoderQuiz"), needs_php=False,
    )

    assert "not used by this project" in _row(rows, "PHP")
    assert "does not use it" in _row(rows, "PATH")
    assert "static server" in _row(rows, "Validation")
    assert "Nothing needs to be installed" in _row(rows, "Validation")


def test_a_static_project_is_ready_even_without_php():
    rows = build_environment_rows(
        _status(available=False), project_root=Path("D:/GitHub/CoderQuiz"),
        project_kind="standard", document_root=Path("D:/GitHub/CoderQuiz"), needs_php=False,
    )

    assert "Nothing needs to be installed" in _row(rows, "Validation")


def test_a_php_project_without_php_is_still_flagged():
    rows = build_environment_rows(
        _status(available=False), project_root=Path("D:/GitHub/streamapp"),
        project_kind="laravel", document_root=Path("D:/GitHub/streamapp/public"), needs_php=True,
    )

    assert "PHP is missing" in _row(rows, "Validation")
