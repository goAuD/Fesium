from dataclasses import dataclass, replace
from pathlib import Path

from fesium.core.browser import open_local_url
from fesium.core.database import DatabaseManager, build_table_preview_query, is_read_query
from fesium.core.database_engines import MYSQL_READ_VERBS, MySQLEngine, query_is_read
from fesium.core.environment import summarize_php_environment
from fesium.core.node_project import describe_node_project, detect_node_project
from fesium.core.project_database import ConnectionSettings, DatabaseRequirement, probe_database
from fesium.core.project_detection import detect_project_profile
from fesium.core.runtime_detection import decide_runtime_backend
from fesium.core.security import normalize_existing_directory, validate_single_sql_statement
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
    database_tables: tuple[str, ...] = ()
    database_selected_table: str = ""
    database_selected_table_info: tuple[dict, ...] = ()
    project_needs_php: bool = True
    """Whether serving this project requires PHP, from the detected profile.

    Defaults to True so a state built without a project reads as "PHP matters",
    which is the assumption that cannot hide a missing runtime.
    """
    database_engine: str = "sqlite"
    """Which engine the database view talks to - "sqlite" or "mysql"."""
    database_connection_settings: ConnectionSettings | None = None
    """Server connection settings for a MySQL session.

    Deliberately credential-free: no field of this frozen dataclass may ever
    carry a password, because it gets repr'd into logs and replaced constantly.
    The password lives in one private attribute on the controller instead.
    """
    database_connected: bool = False


class FesiumController:
    def __init__(self, config, cwd: Path, log_limit: int = 200):
        if log_limit <= 0:
            raise ValueError("log_limit must be greater than zero")
        self.config = config
        self.cwd = Path(cwd)
        self.log_limit = log_limit
        self._backend = None
        self._project_database_path: Path | None = None
        # Session-scoped MySQL state. The password is deliberately kept here,
        # on one private attribute - never on ControllerState (which is frozen,
        # replaced constantly and repr'd into logs) and never on disk.
        self._mysql_manager = None
        self._database_password: str | None = None
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
            project_needs_php=True,
            last_error="",
            log_lines=(),
        )

    def append_log(self, message: str) -> None:
        next_lines = (*self.state.log_lines, message)[-self.log_limit :]
        self.state = replace(self.state, log_lines=next_lines)

    @property
    def project_database_available(self) -> bool:
        return self._project_database_path is not None

    def _database_browser_snapshot(self, preferred_table: str = "") -> tuple[tuple[str, ...], str, tuple[dict, ...]]:
        if self._mysql_manager is not None:
            database = self._mysql_manager
        elif self.state.database_path is None:
            return (), "", ()
        else:
            database = DatabaseManager(str(self.state.database_path), read_only=True)
        if not hasattr(database, "list_tables") or not hasattr(database, "get_table_info"):
            return (
                self.state.database_tables,
                self.state.database_selected_table,
                self.state.database_selected_table_info,
            )
        tables = tuple(database.list_tables())
        if not tables:
            return (), "", ()

        resolved_table = preferred_table or self.state.database_selected_table
        if resolved_table not in tables:
            resolved_table = tables[0]

        columns = tuple(database.get_table_info(resolved_table))
        return tables, resolved_table, columns

    def _refresh_database_browser(self, preferred_table: str = "") -> None:
        tables, selected_table, selected_table_info = self._database_browser_snapshot(preferred_table)
        self.state = replace(
            self.state,
            database_tables=tables,
            database_selected_table=selected_table,
            database_selected_table_info=selected_table_info,
        )

    def select_project(self, path: Path) -> bool:
        ok, normalized = normalize_existing_directory(path)
        if not ok:
            message = str(normalized)
            self.state = replace(self.state, last_error=message)
            self.append_log(f"[Fesium] ERROR: {message}")
            return False

        if self._backend is not None:
            self.stop()

        project_root = Path(normalized)
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
            project_needs_php=profile.needs_php,
            database_tables=(),
            database_selected_table="",
            database_selected_table_info=(),
            database_engine="sqlite",
            database_connection_settings=None,
            database_connected=False,
        )
        # A MySQL session belongs to one project selection; switching projects
        # drops it and forgets the password.
        self._mysql_manager = None
        self._database_password = None
        self._refresh_database_browser()
        self._backend = None
        self.append_log(f"Selected project: {profile.root}")
        self.append_log(f"Backend selected: {runtime_decision.backend_kind}")

        if self.config is not None:
            self.config.set("last_project", str(profile.root))
        return True

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
            database_tables=(),
            database_selected_table="",
            database_selected_table_info=(),
        )
        self._refresh_database_browser()
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
            database_tables=(),
            database_selected_table="",
            database_selected_table_info=(),
        )
        self._refresh_database_browser()
        return True

    def set_database_read_only(self, enabled: bool) -> None:
        if self.state.database_connected and enabled != self.state.database_read_only:
            # The read-only session pin is applied when MySQL connects, so a
            # mid-session flip would leave the server enforcing something the
            # flag no longer says. Drop the session; the next connect applies
            # the new setting.
            self.disconnect_mysql()
            self.append_log(
                "[Fesium] MySQL session dropped - reconnect to apply the new read-only setting"
            )
        self.state = replace(self.state, database_read_only=enabled)

    def connect_mysql(self, settings: ConnectionSettings, password: str, *, engine=None) -> bool:
        """Connect to a MySQL server for this session.

        The password lives only in a private attribute here and inside the
        engine built for it - never on ControllerState, never on disk. The
        probe runs first so a dead host fails in under a second instead of
        stalling on the driver's own timeout.
        """
        if not settings.host or not settings.port or not settings.database:
            message = "Host, port and database name are all required to connect to MySQL"
            self._record_database_error(message)
            return False

        requirement = DatabaseRequirement(
            connection="mysql",
            host=settings.host,
            port=settings.port,
            database=settings.database,
        )
        reachable = probe_database(requirement)
        if reachable is False:
            message = (
                f"Nothing is listening at {settings.address}. Start the MySQL server or check "
                f"the host and port, then connect again."
            )
            self._record_database_error(message)
            return False

        engine = engine if engine is not None else MySQLEngine(
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=password,
        )
        manager = DatabaseManager(settings.database, read_only=self.state.database_read_only, engine=engine)
        ok, result = manager.execute("SELECT 1")
        if not ok:
            message = (
                f"MySQL at {settings.address} refused the connection: {result}. "
                f"Check the user, the password and the database name."
            )
            self._record_database_error(message)
            return False

        self._mysql_manager = manager
        self._database_password = password
        self.state = replace(
            self.state,
            database_engine="mysql",
            database_connection_settings=settings,
            database_connected=True,
            database_last_result={"kind": "none"},
            database_last_error="",
            database_tables=(),
            database_selected_table="",
            database_selected_table_info=(),
        )
        self._refresh_database_browser()
        self.append_log(f"[Fesium] Connected to MySQL at {settings.address}")
        return True

    def disconnect_mysql(self) -> bool:
        """Drop the MySQL session and forget the password."""
        if not self.state.database_connected and self._mysql_manager is None:
            return False

        address = ""
        if self.state.database_connection_settings is not None:
            address = self.state.database_connection_settings.address

        self._mysql_manager = None
        self._database_password = None
        self.state = replace(
            self.state,
            database_engine="sqlite",
            database_connection_settings=None,
            database_connected=False,
            database_last_result={"kind": "none"},
            database_last_error="",
            database_tables=(),
            database_selected_table="",
            database_selected_table_info=(),
        )
        suffix = f" at {address}" if address else ""
        self.append_log(f"[Fesium] Disconnected from MySQL{suffix}")
        return True

    def _record_database_error(self, message: str) -> None:
        self.state = replace(
            self.state,
            database_last_error=message,
            database_last_result={"kind": "error", "message": message},
        )
        self.append_log(f"[Fesium] ERROR: {message}")

    def select_database_table(self, table_name: str) -> bool:
        if not table_name:
            return False

        self._refresh_database_browser(preferred_table=table_name)
        return self.state.database_selected_table == table_name

    def preview_database_table(self, limit: int = 100) -> bool:
        if not self.state.database_selected_table:
            message = "Select a table to preview rows"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        query = build_table_preview_query(self.state.database_selected_table, limit=limit)
        return self.run_database_query(query)

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

        if self.state.database_path is None and self._mysql_manager is None:
            message = "No database selected"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        using_mysql = self._mysql_manager is not None
        database = self._mysql_manager if using_mysql else DatabaseManager(
            str(self.state.database_path),
            read_only=self.state.database_read_only,
        )
        # Read verbs are engine knowledge: SHOW and DESCRIBE are reads on
        # MySQL but unknown words to the SQLite verb set.
        classify_read = (
            (lambda q: query_is_read(q, MYSQL_READ_VERBS)) if using_mysql else is_read_query
        )

        if self.state.database_read_only and not classify_read(query):
            message = "Read-only mode: Write operations are disabled"
            self.state = replace(
                self.state,
                database_last_error=message,
                database_last_result={"kind": "error", "message": message},
            )
            return False

        success, result = database.execute(query)
        if not success:
            self.state = replace(
                self.state,
                database_last_error=str(result),
                database_last_result={"kind": "error", "message": str(result)},
            )
            return False

        if classify_read(query):
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
        self._refresh_database_browser(self.state.database_selected_table)
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

    def _start_backend(self, document_root):
        """Start the backend, telling a static server what it is serving.

        Only the static server takes the hint, and only because it is the one
        that has to answer a browser with something when there is no
        index.html to send. PHP has its own answer for that.
        """
        port = self._resolve_port()
        if self.state.backend_kind != "static":
            return self._backend.start(document_root, port)

        root = self.state.project_root
        hints = describe_node_project(detect_node_project(root)) if root else []
        return self._backend.start(document_root, port, hints=hints)

    def start(self) -> bool:
        if not self.state.document_root:
            self.state = replace(
                self.state,
                server_status="error",
                last_error="No project selected",
            )
            self.append_log("[Fesium] ERROR: No project selected")
            return False

        ok, normalized_document_root = normalize_existing_directory(self.state.document_root)
        if not ok:
            message = str(normalized_document_root)
            self.state = replace(
                self.state,
                server_status="error",
                last_error=message,
                local_url="",
            )
            self.append_log(f"[Fesium] ERROR: {message}")
            return False

        if self._backend is None:
            self._backend = self._build_backend()

        try:
            result = self._start_backend(normalized_document_root)
        except Exception as exc:
            backend_message = getattr(self._backend, "last_error", "")
            message = backend_message or str(exc) or exc.__class__.__name__
            self.state = replace(
                self.state,
                server_status="error",
                last_error=message,
                local_url="",
            )
            self.append_log(f"[Fesium] ERROR: {message}")
            return False

        if not result:
            message = getattr(self._backend, "last_error", "") or "Failed to start server"
            self.state = replace(
                self.state,
                server_status="error",
                last_error=message,
                local_url="",
            )
            self.append_log(f"[Fesium] ERROR: {message}")
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
