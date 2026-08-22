from pathlib import Path

from fesium.core.project_detection import ProjectProfile
from fesium.core.runtime_detection import RuntimeDecision, decide_runtime_backend


def _profile(*, needs_php: bool, kind: str = "standard") -> ProjectProfile:
    return ProjectProfile(
        root=Path("C:/Projects/demo"),
        kind=kind,
        document_root=Path("C:/Projects/demo"),
        database_path=None,
        needs_php=needs_php,
    )


def test_decide_runtime_backend_uses_php_for_a_project_that_needs_it():
    decision = decide_runtime_backend(_profile(needs_php=True), php_available=True)

    assert isinstance(decision, RuntimeDecision)
    assert decision.backend_kind == "php"
    assert decision.reason == "php_available_for_standard"


def test_a_static_project_is_served_statically_even_when_php_is_installed():
    """The decision follows the project, not the machine.

    Fesium used to pick PHP whenever PHP was on PATH, so a plain HTML and
    JavaScript site got a PHP process it had no use for - and the static
    server was only ever a fallback, despite the Guide calling it a
    first-class workflow.
    """
    decision = decide_runtime_backend(_profile(needs_php=False), php_available=True)

    assert decision.backend_kind == "static"
    assert decision.reason == "no_php_needed_for_standard"


def test_a_static_project_needs_no_php_to_run_at_all():
    decision = decide_runtime_backend(_profile(needs_php=False), php_available=False)

    assert decision.backend_kind == "static"


def test_a_php_project_falls_back_to_static_when_php_is_missing():
    """Reduced functionality, but something rather than nothing."""
    decision = decide_runtime_backend(_profile(needs_php=True, kind="laravel"), php_available=False)

    assert decision.backend_kind == "static"
    assert decision.reason == "php_unavailable"
