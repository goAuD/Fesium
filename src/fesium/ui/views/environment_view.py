import customtkinter as ctk

from fesium._version import __version__
from fesium.core.project_database import DatabaseReadiness, describe_database_readiness
from fesium.core.setup_report import build_setup_report, render_setup_report
from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.bento import BentoGrid
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.button import Button
from fesium.ui.widgets.meta_list import MetaList
from fesium.ui.widgets.tile import Tile
from fesium.ui.widgets.view_header import HEADER_GAP, ViewHeader


def build_environment_rows(
    status,
    *,
    project_root=None,
    project_kind: str = "",
    document_root=None,
    needs_php: bool = True,
):
    """Runtime and workspace facts, framed by what this project actually needs.

    PHP used to be reported the same way whatever was open, so a plain HTML
    and JavaScript project was told about a PHP install it has no use for -
    and a machine can carry more than one, which is why the binary's path is
    reported rather than the version alone.
    """
    if not status.php_available:
        path_hint = "Install PHP and add it to PATH to enable PHP-backed local serving"
    elif needs_php:
        path_hint = "PHP is available on PATH for PHP-backed local serving"
    else:
        path_hint = "PHP is installed, but this project does not use it"

    if not project_root:
        validation_message = "Select a project folder to evaluate runtime readiness."
        project_summary = "No project selected"
    else:
        project_summary = f"{project_kind.title()} project at {project_root}"
        if not needs_php:
            validation_message = (
                "This project is served by the static server. Nothing needs to be installed for it to run."
            )
        elif not status.php_available and project_kind == "laravel":
            validation_message = (
                "PHP is missing. Laravel can only use the reduced static fallback "
                "for the public directory."
            )
        elif not status.php_available:
            validation_message = "PHP is missing. Fesium will serve this project statically instead."
        else:
            validation_message = "Workspace and PHP runtime look ready for local serving."

    if status.php_available:
        php_value = "Available" if needs_php else "Available, not used by this project"
    else:
        php_value = "Missing from PATH"

    return [
        {"label": "PHP", "value": php_value},
        {"label": "Version", "value": status.php_version or "Unavailable"},
        # A machine can carry several PHP installs - a standalone one and a
        # leftover from Laragon or XAMPP are common - and PATH decides which
        # Fesium gets. The version alone does not say which.
        {"label": "Binary", "value": getattr(status, "path", "") or "Not resolved"},
        {"label": "PATH", "value": path_hint},
        {"label": "Project Detection", "value": project_summary},
        {"label": "Document Root", "value": str(document_root) if document_root else "Not selected"},
        {"label": "Validation", "value": validation_message},
    ]


def split_environment_rows(rows) -> tuple[list, list]:
    """Runtime facts on the left, workspace facts on the right."""
    runtime_labels = {"PHP", "Version", "Binary", "PATH"}
    runtime = [row for row in rows if row["label"] in runtime_labels]
    workspace = [row for row in rows if row["label"] not in runtime_labels]
    return runtime, workspace


def _runtime_badge(status, needs_php: bool) -> tuple[str, str]:
    """A missing PHP is only a problem for a project that wants PHP."""
    if not needs_php:
        return ("No Runtime Needed", "accent.success")
    if status.php_available:
        return ("PHP Ready", "accent.success")
    return ("PHP Missing", "accent.danger")


class EnvironmentView(ctk.CTkFrame):
    """Environment diagnostics: is the runtime ready, is the workspace ready."""

    def __init__(
        self,
        master,
        status,
        *,
        project_root=None,
        project_kind: str = "",
        document_root=None,
        database_readiness: DatabaseReadiness | None = None,
        needs_php: bool = True,
        backend: str = "",
        port: int | None = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        rows = build_environment_rows(
            status,
            needs_php=needs_php,
            project_root=project_root,
            project_kind=project_kind,
            document_root=document_root,
        )
        runtime_rows, workspace_rows = split_environment_rows(rows)

        header = ViewHeader(
            self,
            "Diagnostics",
            "Runtime checks and project readiness",
            badges=(_runtime_badge(status, needs_php),),
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, HEADER_GAP))

        grid = BentoGrid(self)
        grid.grid(row=1, column=0, sticky="nsew")

        if not needs_php:
            runtime_meta = "not needed here"
        elif status.php_available:
            runtime_meta = "detected"
        else:
            runtime_meta = "not detected"
        runtime = Tile(grid, "PHP Runtime", meta=runtime_meta)
        MetaList(runtime.body, tuple((row["label"], row["value"]) for row in runtime_rows)).grid(
            row=0, column=0, sticky="new"
        )
        grid.place_tile(runtime, row=0, column=0, span=6, row_weight=1)

        workspace = Tile(grid, "Workspace Readiness", meta=project_kind.title() if project_kind else "no project")
        MetaList(workspace.body, tuple((row["label"], row["value"]) for row in workspace_rows)).grid(
            row=0, column=0, sticky="new"
        )
        grid.place_tile(workspace, row=0, column=6, span=6, row_weight=1)

        grid.place_tile(self._build_database_tile(grid, database_readiness), row=1, column=0, span=12)

        self._report = build_setup_report(
            status,
            version=__version__,
            project_root=project_root,
            project_kind=project_kind,
            document_root=document_root,
            needs_php=needs_php,
            backend=backend,
            port=port,
            readiness=database_readiness,
        )
        grid.place_tile(self._build_report_tile(grid), row=2, column=0, span=12)

    def _build_database_tile(self, parent, database_readiness):
        """What the project's own config asks for, and whether it is there.

        Fesium serves PHP but runs no database server, so a project pointed at
        MySQL starts and then fails on its first query. This is the warning
        that used to arrive as a framework stack trace.
        """
        readiness = database_readiness or DatabaseReadiness(requirement=None, reachable=None)
        described = describe_database_readiness(readiness)

        tile = Tile(parent, "Project Database", meta=described["meta"], meta_tone=described["tone"])
        label = ctk.CTkLabel(
            tile.body,
            text=described["label"],
            text_color=get_color_token(described["tone"]),
            font=get_font_token("body_medium"),
            anchor="w",
        )
        label.grid(row=0, column=0, sticky="w")

        detail = BodyText(tile.body, described["detail"], tone="text.secondary")
        detail.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        return tile

    def _build_report_tile(self, parent):
        """Everything above, as one block of text that can be handed to someone.

        A student who is stuck asks a teacher, and what follows is five rounds
        of "which PHP", "where is the project", "is MySQL running" - answers
        that are already on this screen. Copying them turns that into one
        paste. Paths are shortened to ~ and no credential is ever included,
        because the whole point is that this text gets sent somewhere.
        """
        tile = Tile(parent, "Setup Report", meta="for sharing")
        tile.body.grid_columnconfigure(0, weight=1)

        BodyText(
            tile.body,
            "Copy everything on this screen as plain text, to paste into a message "
            "when you ask for help. Your home folder is shortened to ~ and no "
            "password is included.",
            tone="text.secondary",
        ).grid(row=0, column=0, sticky="ew")

        self._report_feedback = ctk.CTkLabel(
            tile.body,
            text="",
            text_color=get_color_token("accent.success"),
            font=get_font_token("meta"),
            anchor="w",
        )
        self._report_feedback.grid(row=1, column=0, sticky="w", pady=(10, 0))

        Button(
            tile.body,
            "Copy Setup Report",
            variant="secondary",
            command=self._copy_report,
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        return tile

    def _copy_report(self) -> None:
        """Put the report on the clipboard, and say so.

        ``update()`` is required: Tk owns the clipboard only while the app is
        running, and without flushing the event queue the contents are not
        available to another application yet.
        """
        text = render_setup_report(self._report)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        lines = len(text.splitlines())
        self._report_feedback.configure(text=f"Copied {lines} lines to the clipboard.")
