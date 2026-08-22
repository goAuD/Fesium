from pathlib import Path

import pytest

from fesium.core.environment import EnvironmentStatus
from fesium.core.setup_report import render_setup_report
from fesium.ui.views.environment_view import EnvironmentView, build_environment_rows


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


# --- the Copy button, which needs a display ---------------------------------


@pytest.fixture(scope="session")
def tk_root():
    """One Tk root for the whole session.

    Destroying a root leaves the interpreter unable to create another, so every
    test after the first would skip for a reason unrelated to the display.
    """
    ctk = pytest.importorskip("customtkinter")
    try:
        root = ctk.CTk()
    except Exception as exc:  # pragma: no cover - depends on the machine
        pytest.skip(f"no display available: {exc}")

    root.geometry("1100x760")
    try:
        yield root
    finally:
        root.destroy()


def _copy_button(widget):
    from fesium.ui.widgets.button import Button

    def walk(node):
        yield node
        for child in node.winfo_children():
            yield from walk(child)

    return next(w for w in walk(widget)
                if isinstance(w, Button) and w.cget("text") == "Copy Setup Report")


def test_copy_button_puts_the_rendered_report_on_the_clipboard(tk_root):
    """The wiring, not the text - build_setup_report is covered headlessly.

    Worth its own check because the button reports success either way: it says
    "Copied" from a handler that could be putting nothing anywhere.
    """
    view = EnvironmentView(
        tk_root,
        _status(),
        project_root=Path("D:/site"),
        project_kind="standard",
        document_root=Path("D:/site"),
        needs_php=False,
        backend="static",
        port=8000,
    )
    view.pack(fill="both", expand=True)
    tk_root.update_idletasks()

    tk_root.clipboard_clear()
    _copy_button(view).invoke()

    copied = tk_root.clipboard_get()
    assert copied == render_setup_report(view._report)
    assert copied.startswith("Fesium setup report")
    assert "lines to the clipboard" in view._report_feedback.cget("text")

    view.destroy()
