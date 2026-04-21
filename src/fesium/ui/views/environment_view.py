import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody


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
        validation_message = "PHP is missing. Laravel can only use the reduced static fallback for the public directory."
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


class EnvironmentView(ctk.CTkFrame):
    """Environment diagnostics view."""

    def __init__(self, master, status, *, project_root=None, project_kind: str = "", document_root=None):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Diagnostics",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Runtime checks and project readiness",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 20))

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        rows = build_environment_rows(
            status,
            project_root=project_root,
            project_kind=project_kind,
            document_root=document_root,
        )
        sections = (
            ("PHP Runtime", rows[:3]),
            ("Workspace Readiness", rows[3:]),
        )

        for section_index, (section_title, section_rows) in enumerate(sections):
            panel = PanelCard(body, surface_variant="inset")
            panel.grid(row=section_index, column=0, sticky="ew", pady=(0, 16) if section_index == 0 else 0)
            panel_content = panel.content_frame

            title_label = ctk.CTkLabel(
                panel_content,
                text=section_title,
                text_color=get_color_token("accent.primary"),
                font=get_font_token("section_heading"),
            )
            title_label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

            for row_index, row in enumerate(section_rows, start=1):
                label = ctk.CTkLabel(
                    panel_content,
                    text=row["label"],
                    text_color=get_color_token("text.primary"),
                    font=get_font_token("body_medium"),
                )
                label.grid(row=row_index * 2 - 1, column=0, sticky="w", padx=16, pady=(8, 4))

                value = ctk.CTkLabel(
                    panel_content,
                    text=row["value"],
                    text_color=get_color_token("text.secondary"),
                    font=get_font_token("body"),
                    justify="left",
                    wraplength=820,
                )
                value.grid(
                    row=row_index * 2,
                    column=0,
                    sticky="w",
                    padx=16,
                    pady=(0, 4 if row_index < len(section_rows) else 16),
                )
