from dataclasses import dataclass
from pathlib import Path

# Directories that are never the project's own source, and are usually the
# largest thing in the tree.
IGNORED_DIRECTORIES = frozenset(
    {"node_modules", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}
)

# A PHP project announces itself at the top: Laravel's artisan, Composer's
# manifest, or an index.php. Checking those first means the common cases cost
# nothing.
PHP_MARKERS = ("artisan", "composer.json", "index.php")

# If the markers are absent, look for a .php file - but only near the surface.
# A full walk of a large folder took 6.4 seconds, and this runs when a project
# is selected.
PHP_SCAN_DEPTH = 2
PHP_SCAN_ENTRIES = 400


@dataclass(frozen=True)
class ProjectProfile:
    root: Path
    kind: str
    document_root: Path
    database_path: Path | None
    needs_php: bool = True
    """Whether serving this project requires PHP.

    Defaults to True because PHP's built-in server also serves static files,
    so it is the answer that cannot break a site if something constructs a
    profile without looking.
    """


def project_needs_php(root: Path, *, depth: int = PHP_SCAN_DEPTH, entries: int = PHP_SCAN_ENTRIES) -> bool:
    """Does serving this project need PHP, or would a static server do?

    Asked about the project rather than the machine. Fesium used to pick PHP
    whenever PHP was installed, which meant a plain HTML and JavaScript site
    was served by a PHP process it had no use for - and made the static server
    a fallback, despite the Guide calling it a first-class workflow.

    An unreadable or enormous folder answers True: PHP serves static files
    too, so it is the choice that cannot break a site.
    """
    root = Path(root)
    if any((root / marker).exists() for marker in PHP_MARKERS):
        return True

    seen = 0
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        current, level = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue

        for child in children:
            seen += 1
            if seen > entries:
                return True

            if child.is_dir():
                if level < depth and child.name not in IGNORED_DIRECTORIES and not child.name.startswith("."):
                    stack.append((child, level + 1))
            elif child.suffix.lower() == ".php":
                return True

    return False


def detect_project_profile(root: Path) -> ProjectProfile:
    resolved_root = Path(root).resolve()

    if (resolved_root / "artisan").exists():
        database_path = resolved_root / "database" / "database.sqlite"
        return ProjectProfile(
            root=resolved_root,
            kind="laravel",
            document_root=resolved_root / "public",
            database_path=database_path if database_path.exists() else None,
            needs_php=True,
        )

    database_path = resolved_root / "database.sqlite"
    return ProjectProfile(
        root=resolved_root,
        kind="standard",
        document_root=resolved_root,
        database_path=database_path if database_path.exists() else None,
        needs_php=project_needs_php(resolved_root),
    )
