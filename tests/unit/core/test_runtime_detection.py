from pathlib import Path

from fesium.core.project_detection import ProjectProfile
from fesium.core.runtime_detection import RuntimeDecision, decide_runtime_backend


def test_decide_runtime_backend_prefers_php_when_available():
    profile = ProjectProfile(
        root=Path("C:/Projects/demo"),
        kind="standard",
        document_root=Path("C:/Projects/demo"),
        database_path=None,
    )

    decision = decide_runtime_backend(profile, php_available=True)

    assert isinstance(decision, RuntimeDecision)
    assert decision.backend_kind == "php"


def test_decide_runtime_backend_falls_back_to_static_without_php():
    profile = ProjectProfile(
        root=Path("C:/Projects/demo"),
        kind="standard",
        document_root=Path("C:/Projects/demo"),
        database_path=None,
    )

    decision = decide_runtime_backend(profile, php_available=False)

    assert decision.backend_kind == "static"
    assert decision.reason == "php_unavailable"
