from dataclasses import dataclass, replace
from pathlib import Path

from fesium.core.browser import open_local_url
from fesium.core.environment import summarize_php_environment
from fesium.core.project_detection import detect_project_profile
from fesium.core.runtime_detection import decide_runtime_backend
from fesium.core.server import PHPServer
from fesium.core.static_server import StaticServer


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
        self._backend = None
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
        if self._backend is not None:
            self.stop()

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
        self._backend = None
        self.append_log(f"Selected project: {profile.root}")
        self.append_log(f"Backend selected: {runtime_decision.backend_kind}")

        if self.config is not None:
            self.config.set("last_project", str(profile.root))

    def _build_backend(self):
        if self.state.backend_kind == "php":
            return PHPServer(on_log=self.append_log)
        if self.state.backend_kind == "static":
            return StaticServer(on_log=self.append_log)
        raise ValueError(f"Unsupported backend kind: {self.state.backend_kind}")

    def _resolve_port(self) -> int:
        if self.config is None:
            return 8000
        if hasattr(self.config, "port"):
            return int(self.config.port)
        if hasattr(self.config, "get"):
            return int(self.config.get("port", 8000))
        return 8000

    def start(self) -> bool:
        if not self.state.document_root:
            self.state = replace(
                self.state,
                server_status="error",
                last_error="No project selected",
            )
            self.append_log("[Fesium] ERROR: No project selected")
            return False

        if self._backend is None:
            self._backend = self._build_backend()

        try:
            result = self._backend.start(self.state.document_root, self._resolve_port())
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            self.state = replace(
                self.state,
                server_status="error",
                last_error=message,
                local_url="",
            )
            self.append_log(f"[Fesium] ERROR: {message}")
            return False

        if not result:
            self.state = replace(
                self.state,
                server_status="error",
                last_error="Failed to start server",
                local_url="",
            )
            self.append_log("[Fesium] ERROR: Failed to start server")
            return False

        local_url = result if isinstance(result, str) else getattr(self._backend, "url", "")
        self.state = replace(
            self.state,
            server_status="running",
            local_url=local_url,
            last_error="",
        )
        return True

    def stop(self) -> bool:
        if self._backend is None:
            self.state = replace(
                self.state,
                server_status="stopped",
                local_url="",
                last_error="",
            )
            return False

        self._backend.stop()
        self.state = replace(
            self.state,
            server_status="stopped",
            local_url="",
            last_error="",
        )
        return True

    def restart(self) -> bool:
        if self.state.server_status != "running":
            self.append_log("[Fesium] Restart rejected: server not running")
            return False

        self.stop()
        return self.start()

    def open_in_browser(self) -> bool:
        if self.state.server_status != "running" or not self.state.local_url:
            self.append_log("[Fesium] Open in Browser rejected: server not running")
            return False
        return open_local_url(self.state.local_url)
