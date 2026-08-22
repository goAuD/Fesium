"""Produce the README screenshots, at exact colours and identical sizes.

    python scripts/capture_screenshots.py
    python scripts/capture_screenshots.py --project "D:/GitHub/CoderQuiz"

Hand-captured screenshots have three problems this avoids:

* **Colour.** Windows' own snipping tool shifted every channel by about +17,
  so the app's ground rendered #23252a instead of #121419 and the whole thing
  looked washed out. Grabbing the pixels directly keeps them exact, and this
  script verifies that rather than trusting it.
* **Rounded corners.** Windows 11 rounds the window *frame*. Capturing the
  client area sidesteps it: that rectangle is square, and it excludes the
  title bar too.
* **Size.** Cropping by hand gave 1245x795 and 1247x797. Every image here is
  the same size because the window is set to it.

`--project` puts a real path on screen instead of the placeholder, which is
worth doing if the screenshot is meant to show actual use.
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import ImageGrab  # noqa: E402

from fesium.core.environment import EnvironmentStatus  # noqa: E402
from fesium.core.project_detection import ProjectProfile  # noqa: E402
from fesium.ui.shell import FesiumShell  # noqa: E402
from fesium.ui.theme.tokens import COLOR_TOKENS  # noqa: E402
from fesium.ui.views.database_view import DatabaseView  # noqa: E402
from fesium.ui.views.environment_view import EnvironmentView  # noqa: E402
from fesium.ui.views.guide_view import GuideView  # noqa: E402
from fesium.ui.views.overview_view import OverviewView  # noqa: E402
from fesium.ui.views.server_view import ServerView  # noqa: E402
from fesium.ui.views.settings_view import SettingsView  # noqa: E402

OUTPUT_DIR = ROOT / "docs" / "assets" / "screenshots"
CAPTURE_SIZE = (1280, 820)

# Windows 11 rounds the window frame, and a pixel or two of that curve can
# reach into the client rectangle at the corners. Trimming a hair removes it
# without touching anything that matters.
CORNER_TRIM = 2

README_VIEWS = ("overview", "server")


def build_shell(project_root: Path) -> FesiumShell:
    profile = ProjectProfile(
        root=project_root,
        kind="laravel",
        document_root=project_root / "public",
        database_path=project_root / "database" / "database.sqlite",
    )
    environment = EnvironmentStatus(True, "PHP 8.5.2 (cli)", "PHP 8.5.2 (cli)")
    logs = (
        f"Selected project: {project_root}",
        "Backend selected: php",
        "[Fesium] Started at http://localhost:8000",
        f"[Fesium] Document root: {profile.document_root}",
        "[127.0.0.1:51422] GET /  - Accepted",
        "[127.0.0.1:51422] GET /css/app.css - Accepted",
    )

    shell = FesiumShell()
    shell.geometry(f"{CAPTURE_SIZE[0]}x{CAPTURE_SIZE[1]}+40+40")
    shell.register_view("overview", lambda parent: OverviewView(
        parent, project_root=profile.root, project_kind=profile.kind,
        php_summary=environment.summary, server_status="running",
        local_url="http://localhost:8000", log_lines=logs))
    shell.register_view("server", lambda parent: ServerView(
        parent, document_root=profile.document_root, port=8000, project_root=profile.root,
        project_kind=profile.kind, backend_kind="php", server_status="running",
        local_url="http://localhost:8000", last_error="", log_lines=logs))
    shell.register_view("database", lambda parent: DatabaseView(
        parent, db_path=str(profile.database_path), read_only=True, source="project",
        project_database_available=True,
        tables=("failed_jobs", "migrations", "password_resets", "sessions", "users"),
        selected_table="users",
        selected_table_info=(
            {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
            {"name": "name", "type": "TEXT", "nullable": False, "primary_key": False},
            {"name": "email", "type": "TEXT", "nullable": False, "primary_key": False},
            {"name": "created_at", "type": "TEXT", "nullable": True, "primary_key": False},
        ),
        last_query="SELECT id, name, email FROM users LIMIT 5",
        last_result={
            "kind": "read",
            "columns": ["id", "name", "email"],
            "rows": [
                (1, "Ada Lovelace", "ada@example.test"),
                (2, "Linus Torvalds", "linus@example.test"),
                (3, "Grace Hopper", "grace@example.test"),
            ],
            "count": 3,
        },
    ))
    shell.register_view("environment", lambda parent: EnvironmentView(
        parent, status=environment, project_root=profile.root,
        project_kind=profile.kind, document_root=profile.document_root))
    shell.register_view("guide", lambda parent: GuideView(parent))
    shell.register_view("settings", lambda parent: SettingsView(
        parent, config_data={"port": 8000, "last_project": str(profile.root)}))
    return shell


def settle(shell, rounds: int = 12) -> None:
    """Let the window finish appearing.

    Windows fades a new window in, and grabbing during that animation captures
    a half-transparent window composited over whatever is behind it.
    """
    for _ in range(rounds):
        shell.update_idletasks()
        shell.update()
        time.sleep(0.08)


def capture(shell, view_id: str) -> "tuple[Path, tuple[int, int]]":
    shell.set_active_view(view_id)
    settle(shell, rounds=6)

    x, y = shell.winfo_rootx() + CORNER_TRIM, shell.winfo_rooty() + CORNER_TRIM
    width = shell.winfo_width() - 2 * CORNER_TRIM
    height = shell.winfo_height() - 2 * CORNER_TRIM
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height)).convert("RGB")

    target = OUTPUT_DIR / f"fesium-{view_id}.png"
    image.save(target)
    return target, image.size


def verify_colours(path: Path) -> bool:
    """The ground in the image must be exactly the ground in the palette.

    This is the check that catches a colour-managed capture: the snipping tool
    shifted every channel by about +17, which looks fine until compared.
    """
    from PIL import Image

    image = Image.open(path).convert("RGB")
    dominant, _count = Counter(image.get_flattened_data()).most_common(1)[0]
    expected = tuple(int(COLOR_TOKENS["bg.app"][i : i + 2], 16) for i in (1, 3, 5))
    drift = max(abs(a - b) for a, b in zip(dominant, expected, strict=True))

    got = "#{:02x}{:02x}{:02x}".format(*dominant)
    if drift == 0:
        print(f"       colours exact ({got} == bg.app)")
        return True
    print(f"       COLOUR DRIFT: {got} vs bg.app {COLOR_TOKENS['bg.app']}, off by {drift} per channel")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="C:/Projects/student-portal",
                        help="project path to show on screen")
    parser.add_argument("--views", nargs="*", default=list(README_VIEWS),
                        help="which views to capture")
    arguments = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        shell = build_shell(Path(arguments.project))
    except Exception as exc:  # pragma: no cover - depends on the machine
        print(f"cannot open a window: {exc}")
        return 1

    shell.lift()
    shell.attributes("-topmost", True)
    settle(shell)

    sizes = set()
    exact = True
    try:
        for view_id in arguments.views:
            target, size = capture(shell, view_id)
            sizes.add(size)
            print(f"  {view_id:<12} {size[0]}x{size[1]}  ->  {target.relative_to(ROOT).as_posix()}")
            exact &= verify_colours(target)
    finally:
        shell.destroy()

    if len(sizes) == 1:
        print(f"\nall images {sizes.pop()}")
    else:
        print(f"\nSIZES DIFFER: {sorted(sizes)}")
        exact = False
    return 0 if exact else 1


if __name__ == "__main__":
    raise SystemExit(main())
