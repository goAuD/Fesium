import logging
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

from fesium._version import __version__
from fesium.app.controller import FesiumController
from fesium.core.config import Config
from fesium.core.environment import summarize_php_environment
from fesium.core.paths import AppPaths
from fesium.core.preferences import (
    PreferenceResult,
    normalize_default_project,
    normalize_port,
)
from fesium.core.project_database import summarize_project_database
from fesium.core.security import classify_query_risk, validate_single_sql_statement
from fesium.ui.shell import DEFAULT_WINDOW_GEOMETRY, FesiumShell
from fesium.ui.views.database_view import DatabaseView
from fesium.ui.views.environment_view import EnvironmentView
from fesium.ui.views.guide_view import GuideView
from fesium.ui.views.overview_view import OverviewView
from fesium.ui.views.server_view import ServerView
from fesium.ui.views.settings_view import SettingsView

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Install the default console log handler.

    Kept out of module scope so importing :mod:`fesium.app.bootstrap` (for
    tests or for other entrypoints) does not mutate root-logger configuration
    as a side effect. :func:`main` calls it once at startup.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@dataclass(frozen=True)
class AppMetadata:
    name: str
    tagline: str


@dataclass(frozen=True)
class AppContext:
    project_root: Path
    active_view: str


def build_window_title(version: str) -> str:
    return f"Fesium v{version}"


def build_default_paths(home_dir: Path = None) -> AppPaths:
    return AppPaths(home_dir=home_dir or Path.home())


def build_app_context(cwd: Path, config_data: dict[str, str]) -> AppContext:
    """Resolve the folder Fesium opens with, honouring the startup preferences.

    Order: the last project (only when the user asked for it to be restored),
    then the configured default folder, then the working directory. A folder
    that has since been moved or deleted is skipped rather than fatal.
    """
    candidates = []
    if config_data.get("restore_last_project", True):
        candidates.append(config_data.get("last_project"))
    candidates.append(config_data.get("default_project"))

    project_root = cwd.resolve()
    for candidate in candidates:
        if not candidate:
            continue
        resolved = Path(candidate).resolve()
        if resolved.is_dir():
            project_root = resolved
            break

    active_view = config_data.get("active_view", "overview")
    return AppContext(project_root=project_root, active_view=active_view)


def resolve_window_geometry(window_geometry: str | None) -> str:
    if not window_geometry or window_geometry == "1280x860":
        return DEFAULT_WINDOW_GEOMETRY
    return window_geometry


def _build_metadata() -> AppMetadata:
    return AppMetadata(
        name="Fesium",
        tagline="Local dev tools for students and developers",
    )


def _replace_runtime_views(
    *,
    shell: FesiumShell,
    controller: FesiumController,
    config: Config,
    select_project_action,
    start_action,
    stop_action,
    restart_action,
    open_browser_action,
    select_database_action,
    reset_project_database_action,
    toggle_database_read_only_action,
    select_database_table_action=None,
    preview_database_table_action=None,
    run_sql_action=None,
    settings_actions=None,
) -> None:
    state = controller.state

    shell.replace_view(
        "overview",
        lambda parent: OverviewView(
            parent,
            project_root=state.project_root,
            project_kind=state.project_kind,
            php_summary=state.php_summary,
            server_status=state.server_status,
            local_url=state.local_url,
            log_lines=state.log_lines,
            on_start=start_action,
            on_stop=stop_action,
            on_open_browser=open_browser_action,
        ),
    )
    shell.replace_view(
        "server",
        lambda parent: ServerView(
            parent,
            document_root=state.document_root,
            port=config.port,
            project_root=state.project_root,
            project_kind=state.project_kind,
            backend_kind=state.backend_kind,
            server_status=state.server_status,
            local_url=state.local_url,
            last_error=state.last_error,
            log_lines=state.log_lines,
            on_select_project=select_project_action,
            on_start=start_action,
            on_stop=stop_action,
            on_restart=restart_action,
            on_open_browser=open_browser_action,
        ),
    )
    shell.replace_view(
        "database",
        lambda parent: DatabaseView(
            parent,
            db_path=str(state.database_path) if state.database_path else "",
            read_only=state.database_read_only,
            source=state.database_source,
            project_database_available=controller.project_database_available,
            last_query=state.database_last_query,
            last_result=state.database_last_result,
            last_error=state.database_last_error,
            tables=getattr(state, "database_tables", ()),
            selected_table=getattr(state, "database_selected_table", ""),
            selected_table_info=getattr(state, "database_selected_table_info", ()),
            on_select_database=select_database_action,
            on_reset_project_database=reset_project_database_action,
            on_toggle_read_only=toggle_database_read_only_action,
            on_select_table=select_database_table_action,
            on_preview_table=preview_database_table_action,
            on_run_sql=run_sql_action,
        ),
    )
    shell.replace_view(
        "environment",
        # summarize_project_database touches the filesystem and opens a socket,
        # so it runs inside the factory: only when Diagnostics is actually shown,
        # not on every view refresh.
        lambda parent: EnvironmentView(
            parent,
            # Diagnostics re-probes rather than reusing the cached summary.
            # It is the one screen someone opens *because* they just installed
            # PHP, and the factory only runs when the view is shown, so the
            # 78ms is paid where it buys an accurate answer.
            status=summarize_php_environment(max_age=0),
            project_root=state.project_root,
            project_kind=state.project_kind,
            document_root=state.document_root,
            database_readiness=summarize_project_database(state.project_root),
        ),
    )
    shell.replace_view(
        "guide",
        lambda parent: GuideView(parent),
    )
    shell.replace_view(
        "settings",
        lambda parent: SettingsView(
            parent,
            config_data=config.snapshot(),
            **(settings_actions or {}),
        ),
    )


def main() -> None:
    _configure_logging()
    metadata = _build_metadata()
    paths = build_default_paths()
    cwd = Path.cwd()
    config = Config(
        config_dir=paths.config_dir,
        legacy_config_dir=paths.legacy_config_dir,
    )
    context = build_app_context(cwd, config.snapshot())
    controller = FesiumController(config=config, cwd=cwd)
    startup_project = context.project_root if context.project_root else cwd
    controller.select_project(startup_project)

    shell = FesiumShell()
    shell.title(build_window_title(__version__))
    shell.geometry(resolve_window_geometry(config.get("window_geometry")))

    def refresh_runtime_views() -> None:
        _replace_runtime_views(
            shell=shell,
            controller=controller,
            config=config,
            select_project_action=select_project_action,
            start_action=start_action,
            stop_action=stop_action,
            restart_action=restart_action,
            open_browser_action=open_browser_action,
            select_database_action=select_database_action,
            reset_project_database_action=reset_project_database_action,
            toggle_database_read_only_action=toggle_database_read_only_action,
            select_database_table_action=select_database_table_action,
            preview_database_table_action=preview_database_table_action,
            run_sql_action=run_sql_action,
            settings_actions=settings_actions,
        )

    def select_project_action() -> None:
        initial_dir = controller.state.project_root or cwd
        selected_directory = filedialog.askdirectory(
            initialdir=str(initial_dir),
        )
        if not selected_directory:
            return

        controller.select_project(Path(selected_directory))
        refresh_runtime_views()

    def start_action() -> None:
        controller.start()
        refresh_runtime_views()

    def stop_action() -> None:
        controller.stop()
        refresh_runtime_views()

    def restart_action() -> None:
        controller.restart()
        refresh_runtime_views()

    def open_browser_action() -> None:
        controller.open_in_browser()
        refresh_runtime_views()

    def select_database_action() -> None:
        initial_dir = controller.state.database_path or controller.state.project_root or cwd
        selected_file = filedialog.askopenfilename(
            initialdir=str(initial_dir.parent if isinstance(initial_dir, Path) else initial_dir),
            filetypes=(
                ("SQLite Databases", "*.sqlite *.db *.db3"),
                ("All Files", "*.*"),
            ),
        )
        if not selected_file:
            return

        controller.select_database(Path(selected_file))
        refresh_runtime_views()

    def reset_project_database_action() -> None:
        controller.reset_to_project_database()
        refresh_runtime_views()

    def toggle_database_read_only_action(enabled: bool) -> None:
        controller.set_database_read_only(enabled)
        refresh_runtime_views()

    def select_database_table_action(table_name: str) -> None:
        controller.select_database_table(table_name)
        refresh_runtime_views()

    def preview_database_table_action() -> None:
        controller.preview_database_table()
        refresh_runtime_views()

    def run_sql_action(query: str) -> None:
        is_single_statement, _ = validate_single_sql_statement(query)
        if is_single_statement and not controller.state.database_read_only:
            risk = classify_query_risk(query)
            if risk.requires_confirmation:
                confirmed = messagebox.askyesno(
                    "Confirm Destructive Query",
                    "This query may modify or remove data. Do you want to continue?",
                )
                if not confirmed:
                    return

        controller.run_database_query(query)
        refresh_runtime_views()

    def apply_port_action(raw: str) -> PreferenceResult:
        result = normalize_port(raw)
        if result.ok:
            config.port = result.value
        return result

    def select_default_project_action() -> PreferenceResult:
        current = config.default_project
        selected_directory = filedialog.askdirectory(
            initialdir=current or str(controller.state.project_root or cwd),
        )
        if not selected_directory:
            # Cancelled: report the value that is still stored, and say nothing.
            return PreferenceResult(True, current, "")

        result = normalize_default_project(selected_directory)
        if result.ok:
            config.default_project = result.value
        return result

    def clear_default_project_action() -> PreferenceResult:
        result = normalize_default_project("")
        config.default_project = result.value
        return result

    def toggle_restore_last_project_action(enabled: bool) -> PreferenceResult:
        config.restore_last_project = enabled
        message = (
            "Fesium will reopen your last project on the next launch"
            if enabled
            else "Fesium will start from the default project folder"
        )
        return PreferenceResult(True, enabled, message)

    settings_actions = {
        "on_apply_port": apply_port_action,
        "on_select_default_project": select_default_project_action,
        "on_clear_default_project": clear_default_project_action,
        "on_toggle_restore_last_project": toggle_restore_last_project_action,
    }

    refresh_runtime_views()
    requested_view = context.active_view if context.active_view in shell._view_factories else "overview"
    shell.set_active_view(requested_view)

    def on_close() -> None:
        config.set("window_geometry", shell.geometry())
        config.active_view = shell.active_view_id or requested_view
        controller.stop()
        logger.info("%s closed", metadata.name)
        shell.destroy()

    shell.protocol("WM_DELETE_WINDOW", on_close)
    logger.info("%s started", metadata.name)
    shell.mainloop()
