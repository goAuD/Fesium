import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from fesium import __version__
from fesium.core.config import Config
from fesium.core.database import DatabaseManager
from fesium.core.environment import summarize_php_environment
from fesium.core.paths import AppPaths
from fesium.core.project_detection import detect_project_profile
from fesium.core.server import PHPServer
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
    config = Config(
        config_dir=paths.config_dir,
        legacy_config_dir=paths.legacy_config_dir,
    )
    context = build_app_context(Path.cwd(), config._data)
    profile = detect_project_profile(context.project_root)
    database = DatabaseManager(
        str(profile.database_path) if profile.database_path else None,
        read_only=True,
    )
    server = PHPServer()
    server.document_root = str(profile.document_root)
    environment_status = summarize_php_environment()

    shell = FesiumShell()
    shell.title(build_window_title(__version__))
    shell.geometry(config.get("window_geometry", "1280x860"))
    shell.register_view(
        "overview",
        lambda parent: OverviewView(
            parent,
            project_profile=profile,
            php_summary=environment_status.summary,
            server_running=server.is_running,
        ),
    )
    shell.register_view(
        "server",
        lambda parent: ServerView(
            parent,
            document_root=profile.document_root,
            port=config.port,
            is_running=server.is_running,
        ),
    )
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
        if server.is_running:
            server.stop()
        logger.info("%s closed", metadata.name)
        shell.destroy()

    shell.protocol("WM_DELETE_WINDOW", on_close)
    logger.info("%s started", metadata.name)
    shell.mainloop()
