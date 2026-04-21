import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fesium.core.environment import EnvironmentStatus
from fesium.core.project_detection import ProjectProfile
from fesium.ui.shell import DEFAULT_WINDOW_GEOMETRY, FesiumShell
from fesium.ui.views.database_view import DatabaseView
from fesium.ui.views.environment_view import EnvironmentView
from fesium.ui.views.guide_view import GuideView
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
    recent_logs = (
        "Selected project: C:/Projects/student-portal",
        "Backend selected: php",
        "[Fesium] Started at http://localhost:8000",
    )
    config_data = {
        "port": 8000,
        "active_view": "overview",
        "window_geometry": DEFAULT_WINDOW_GEOMETRY,
        "last_project": str(profile.root),
    }

    shell = FesiumShell()
    shell.title("Fesium")
    shell.geometry(DEFAULT_WINDOW_GEOMETRY)

    shell.register_view(
        "overview",
        lambda parent: OverviewView(
            parent,
            project_root=profile.root,
            project_kind=profile.kind,
            php_summary=environment.summary,
            server_status="running",
            local_url="http://localhost:8000",
            log_lines=recent_logs,
        ),
    )
    shell.register_view(
        "server",
        lambda parent: ServerView(
            parent,
            document_root=profile.document_root,
            project_root=profile.root,
            project_kind=profile.kind,
            port=8000,
            backend_kind="php",
            server_status="running",
            local_url="http://localhost:8000",
            log_lines=recent_logs,
        ),
    )
    shell.register_view(
        "database",
        lambda parent: DatabaseView(
            parent,
            db_path=str(profile.database_path),
            read_only=True,
            source="project",
            project_database_available=True,
            tables=("jobs", "migrations", "users"),
            selected_table="users",
            selected_table_info=(
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "email", "type": "TEXT", "nullable": False, "primary_key": False},
                {"name": "created_at", "type": "TEXT", "nullable": True, "primary_key": False},
            ),
            last_query="SELECT id, email FROM users LIMIT 5",
            last_result={
                "kind": "read",
                "columns": ["id", "email"],
                "rows": [(1, "ada@example.test"), (2, "linus@example.test")],
                "count": 2,
            },
        ),
    )
    shell.register_view(
        "environment",
        lambda parent: EnvironmentView(
            parent,
            status=environment,
            project_root=profile.root,
            project_kind=profile.kind,
            document_root=profile.document_root,
        ),
    )
    shell.register_view(
        "guide",
        lambda parent: GuideView(parent),
    )
    shell.register_view(
        "settings",
        lambda parent: SettingsView(parent, config_data=config_data),
    )
    shell.set_active_view("overview")
    shell.mainloop()


if __name__ == "__main__":
    main()
