from dataclasses import dataclass, replace
from pathlib import Path

from fesium.core.browser import open_local_url
from fesium.core.database import DatabaseManager, is_read_query
from fesium.core.environment import summarize_php_environment
from fesium.core.project_detection import detect_project_profile
from fesium.core.runtime_detection import decide_runtime_backend
from fesium.core.security import validate_single_sql_statement
from fesium.core.server import PHPServer
from fesium.core.static_server import StaticServer


@dataclass(frozen=True)
class ControllerState:
    project_root: Path | None
    project_kind: str
    document_root: Path | None
    database_path: Path | None
    database_source: str
    database_read_only: bool
    database_last_query: str
    database_last_result: dict
    database_last_error: str
    backend_kind: str
    server_status: str
    local_url: str
    php_available: bool
    php_summary: str
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
        self._project_database_path: Path | None = None
        self.state = ControllerState(
            project_root=None,
            project_kind="unknown",
            document_root=None,
            database_path=None,
            database_source="none",
            database_read_only=True,
            database_last_query="",
            database_last_result={"kind": "none"},
            database_last_error="",
            backend_kind="none",
            server_status="stopped",
            local_url="",
            php_available=False,
            php_summary="",
            last_error="",
            log_lines=(),
        )

    def append_log(self, message: str) -> None:
        next_lines = (*self.state.log_lines, message)[-self.log_limit :]
        self.state = replace(self.state, log_lines=next_lines)

    @property
    def project_database_available(self) -> bool:
        return self._project_database_path is not None

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
        self._project_database_path = profile.database_path.resolve() if profile.database_path else None
        keep_manual_database = self.state.database_source == "manual" and self.state.database_path is not None
        next_database_path = self.state.database_path if keep_manual_database else self._project_database_path
        next_database_source = (
            "manual"
            if keep_manual_database
            else "project" if next_database_path is not None else "none"
        )

        self.state = replace(
            self.state,
            project_root=profile.root,
            project_kind=profile.kind,
            document_root=profile.document_root,
            database_path=next_database_path,
            database_source=next_database_source,
            database_read_only=True,
            database_last_query="",
            database_last_result={"kind": "none"},
            database_last_error="",
            backend_kind=runtime_decision.backend_kind,
            server_status="stopped",
            local_url="",
            last_error="",
            php_available=environment_status.php_available,
            php_summary=environment_status.summary,
        )
        self._backend = None
        self.append_log(f"Selected project: {profile.root}")
        self.append_log(f"Backend selected: {runtime_decision.backend_kind}")

        if self.config is not None:
            self.config.set("last_project", str(profile.root))

    def select_database(self, path: Path) -> bool:
        candidate = Path(path).expanduser().resolve()
        if not candidate.exists() or not candidate.is_file():
            message = f"Database file not found: {candidate}"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        self.state = replace(
            self.state,
            database_path=candidate,
            database_source="manual",
            database_last_result={"kind": "none"},
            database_last_error="",
        )
        return True

    def reset_to_project_database(self) -> bool:
        if self._project_database_path is None:
            return False

        self.state = replace(
            self.state,
            database_path=self._project_database_path,
            database_source="project",
            database_last_result={"kind": "none"},
            database_last_error="",
        )
        return True

    def set_database_read_only(self, enabled: bool) -> None:
        self.state = replace(self.state, database_read_only=enabled)

    def run_database_query(self, query: str) -> bool:
        self.state = replace(self.state, database_last_query=query)

        ok, validation_message = validate_single_sql_statement(query)
        if not ok:
            self.state = replace(
                self.state,
                database_last_error=validation_message,
                database_last_result={"kind": "error", "message": validation_message},
            )
            return False

        if self.state.database_path is None:
            message = "No database selected"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        if self.state.database_read_only and not is_read_query(query):
            message = "Read-only mode: Write operations are disabled"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        database = DatabaseManager(
            str(self.state.database_path),
            read_only=self.state.database_read_only,
        )
        success, result = database.execute(query)
        if not success:
            self.state = replace(
                self.state,
                database_last_error=str(result),
                database_last_result={"kind": "error", "message": str(result)},
            )
            return False

        if is_read_query(query):
            normalized_result = {
                "kind": "read",
                "columns": result["columns"],
                "rows": result["rows"],
                "count": result["count"],
            }
        else:
            normalized_result = {
                "kind": "write",
                "affected": result["affected"],
            }

        self.state = replace(
            self.state,
            database_last_result=normalized_result,
            database_last_error="",
        )
        return True

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
