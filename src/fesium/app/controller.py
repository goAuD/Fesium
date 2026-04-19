from dataclasses import dataclass, replace
from pathlib import Path

from fesium.core.environment import summarize_php_environment
from fesium.core.project_detection import detect_project_profile
from fesium.core.runtime_detection import decide_runtime_backend


@dataclass(frozen=True)
class ControllerState:
    project_root: Path | None
    project_kind: str
    document_root: Path | None
    backend_kind: str
    server_status: str
    local_url: str
    php_available: bool
    last_error: str
    log_lines: tuple[str, ...]


class FesiumController:
    def __init__(self, config, cwd: Path, log_limit: int = 200):
        if log_limit <= 0:
            raise ValueError("log_limit must be greater than zero")
        self.config = config
        self.cwd = Path(cwd)
        self.log_limit = log_limit
        self.state = ControllerState(
            project_root=None,
            project_kind="unknown",
            document_root=None,
            backend_kind="none",
            server_status="stopped",
            local_url="",
            php_available=False,
            last_error="",
            log_lines=(),
        )

    def append_log(self, message: str) -> None:
        next_lines = (*self.state.log_lines, message)[-self.log_limit :]
        self.state = replace(self.state, log_lines=next_lines)

    def select_project(self, path: Path) -> None:
        project_root = Path(path).resolve()
        profile = detect_project_profile(project_root)
        environment_status = summarize_php_environment()
        runtime_decision = decide_runtime_backend(
            profile,
            php_available=environment_status.php_available,
        )

        self.state = replace(
            self.state,
            project_root=profile.root,
            project_kind=profile.kind,
            document_root=profile.document_root,
            backend_kind=runtime_decision.backend_kind,
            server_status="stopped",
            local_url="",
            last_error="",
            php_available=environment_status.php_available,
        )
        self.append_log(f"Selected project: {profile.root}")
        self.append_log(f"Backend selected: {runtime_decision.backend_kind}")

        if self.config is not None:
            self.config.set("last_project", str(profile.root))
