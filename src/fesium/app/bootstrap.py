import logging
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog
from typing import Dict

from fesium import __version__
from fesium.app.controller import FesiumController
from fesium.core.config import Config
from fesium.core.database import DatabaseManager
from fesium.core.environment import summarize_php_environment
from fesium.core.paths import AppPaths
from fesium.core.project_detection import detect_project_profile
from fesium.ui.shell import FesiumShell
from fesium.ui.views.database_view import DatabaseView
from fesium.ui.views.environment_view import EnvironmentView
from fesium.ui.views.overview_view import OverviewView
from fesium.ui.views.server_view import ServerView
from fesium.ui.views.settings_view import SettingsView


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


def build_app_context(cwd: Path, config_data: Dict[str, str]) -> AppContext:
    project_root = Path(config_data.get("last_project") or cwd).resolve()
    active_view = config_data.get("active_view", "overview")
    return AppContext(project_root=project_root, active_view=active_view)


def _build_metadata() -> AppMetadata:
    return AppMetadata(
        name="Fesium",
        tagline="Local dev tools for students and developers",
    )


def main() -> None:
    metadata = _build_metadata()
    paths = build_default_paths()
    cwd = Path.cwd()
    config = Config(
        config_dir=paths.config_dir,
        legacy_config_dir=paths.legacy_config_dir,
    )
    context = build_app_context(cwd, config._data)
    controller = FesiumController(config=config, cwd=cwd)
    startup_project = context.project_root if context.project_root else cwd
    controller.select_project(startup_project)

    profile = detect_project_profile(controller.state.project_root or startup_project)
    database = DatabaseManager(
        str(profile.database_path) if profile.database_path else None,
        read_only=True,
    )
    environment_status = summarize_php_environment()

    shell = FesiumShell()
    shell.title(build_window_title(__version__))
    shell.geometry(config.get("window_geometry", "1280x860"))

    def refresh_runtime_views() -> None:
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

    refresh_runtime_views()
    shell.register_view(
        "database",
        lambda parent: DatabaseView(
            parent,
            db_path=str(database.db_path) if database.db_path else "",
            read_only=database.read_only,
        ),
    )
    shell.register_view(
        "environment",
        lambda parent: EnvironmentView(parent, status=environment_status),
    )
    shell.register_view(
        "settings",
        lambda parent: SettingsView(parent, config_data=config._data),
    )
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
