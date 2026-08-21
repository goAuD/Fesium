import customtkinter as ctk

from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.meta_list import MetaList
from fesium.ui.widgets.tile import Tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader


def build_environment_rows(
    status,
    *,
    project_root=None,
    project_kind: str = "",
    document_root=None,
):
    if status.php_available:
        path_hint = "PHP is available on PATH for PHP-backed local serving"
    else:
        path_hint = "Install PHP and add it to PATH to enable PHP-backed local serving"

    if not project_root:
        validation_message = "Select a project folder to evaluate runtime readiness."
        project_summary = "No project selected"
    elif not status.php_available and project_kind == "laravel":
        validation_message = (
            "PHP is missing. Laravel can only use the reduced static fallback "
            "for the public directory."
        )
        project_summary = f"{project_kind.title()} project at {project_root}"
    elif not status.php_available:
        validation_message = "PHP is missing. Fesium will use the static fallback for standard sites."
        project_summary = f"{project_kind.title()} project at {project_root}"
    else:
        validation_message = "Workspace and PHP runtime look ready for local serving."
        project_summary = f"{project_kind.title()} project at {project_root}"

    return [
        {"label": "PHP", "value": "Available" if status.php_available else "Missing from PATH"},
        {"label": "Version", "value": status.php_version or "Unavailable"},
        {"label": "PATH", "value": path_hint},
        {"label": "Project Detection", "value": project_summary},
        {"label": "Document Root", "value": str(document_root) if document_root else "Not selected"},
        {"label": "Validation", "value": validation_message},
    ]


def split_environment_rows(rows) -> tuple[list, list]:
    """Runtime facts on the left, workspace facts on the right."""
    runtime_labels = {"PHP", "Version", "PATH"}
    runtime = [row for row in rows if row["label"] in runtime_labels]
    workspace = [row for row in rows if row["label"] not in runtime_labels]
    return runtime, workspace


class EnvironmentView(ctk.CTkFrame):
    """Environment diagnostics: is the runtime ready, is the workspace ready."""

    def __init__(self, master, status, *, project_root=None, project_kind: str = "", document_root=None):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        rows = build_environment_rows(
            status,
            project_root=project_root,
            project_kind=project_kind,
            document_root=document_root,
        )
        runtime_rows, workspace_rows = split_environment_rows(rows)

        header = ViewHeader(
            self,
            "Diagnostics",
            "Runtime checks and project readiness",
            badges=(
                ("PHP Ready", "accent.success") if status.php_available else ("PHP Missing", "accent.danger"),
            ),
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        runtime = Tile(grid, "PHP Runtime", meta=status.php_version or "not detected")
        MetaList(runtime.body, tuple((row["label"], row["value"]) for row in runtime_rows)).grid(
            row=0, column=0, sticky="new"
        )
        grid.place_tile(runtime, row=0, column=0, span=6, row_weight=1)

        workspace = Tile(grid, "Workspace Readiness", meta=project_kind.title() if project_kind else "no project")
        MetaList(workspace.body, tuple((row["label"], row["value"]) for row in workspace_rows)).grid(
            row=0, column=0, sticky="new"
        )
        grid.place_tile(workspace, row=0, column=6, span=6, row_weight=1)
