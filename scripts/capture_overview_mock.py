import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fesium.core.environment import EnvironmentStatus
from fesium.core.project_detection import ProjectProfile
from fesium.ui.shell import FesiumShell
from fesium.ui.views.database_view import DatabaseView
from fesium.ui.views.environment_view import EnvironmentView
from fesium.ui.views.overview_view import OverviewView
from fesium.ui.views.server_view import ServerView
from fesium.ui.views.settings_view import SettingsView


def build_mock_profile() -> ProjectProfile:
    root = Path("C:/Projects/student-portal")
    return ProjectProfile(
        root=root,
        kind="laravel",
        document_root=root / "public",
        database_path=root / "database" / "database.sqlite",
    )


def build_mock_environment() -> EnvironmentStatus:
    return EnvironmentStatus(
        php_available=True,
        php_version="PHP 8.3.7 (cli)",
        summary="PHP 8.3.7 (cli)",
    )


def main() -> None:
    profile = build_mock_profile()
    environment = build_mock_environment()
    config_data = {
        "port": 8000,
        "active_view": "overview",
    }

    shell = FesiumShell()
    shell.title("Fesium")
    shell.geometry("1280x860")

    shell.register_view(
        "overview",
        lambda parent: OverviewView(
            parent,
            project_profile=profile,
            php_summary=environment.summary,
            server_running=False,
        ),
    )
    shell.register_view(
        "server",
        lambda parent: ServerView(
            parent,
            document_root=profile.document_root,
            port=8000,
            is_running=False,
        ),
    )
    shell.register_view(
        "database",
        lambda parent: DatabaseView(
            parent,
            db_path=str(profile.database_path),
            read_only=True,
        ),
    )
    shell.register_view(
        "environment",
        lambda parent: EnvironmentView(parent, status=environment),
    )
    shell.register_view(
        "settings",
        lambda parent: SettingsView(parent, config_data=config_data),
    )
    shell.set_active_view("overview")
    shell.mainloop()


if __name__ == "__main__":
    main()
