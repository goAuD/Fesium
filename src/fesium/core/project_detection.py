from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProjectProfile:
    root: Path
    kind: str
    document_root: Path
    database_path: Optional[Path]


def detect_project_profile(root: Path) -> ProjectProfile:
    resolved_root = Path(root).resolve()

    if (resolved_root / "artisan").exists():
        database_path = resolved_root / "database" / "database.sqlite"
        return ProjectProfile(
            root=resolved_root,
            kind="laravel",
            document_root=resolved_root / "public",
            database_path=database_path if database_path.exists() else None,
        )

    database_path = resolved_root / "database.sqlite"
    return ProjectProfile(
        root=resolved_root,
        kind="standard",
        document_root=resolved_root,
        database_path=database_path if database_path.exists() else None,
    )
