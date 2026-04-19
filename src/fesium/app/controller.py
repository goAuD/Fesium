from dataclasses import dataclass, replace
from pathlib import Path


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
