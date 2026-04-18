import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.status_badge import StatusBadge


def build_database_summary(db_path: str, read_only: bool):
    return {
        "path": db_path or "No database selected",
        "badge": "Read-only Enabled" if read_only else "Write Mode",
        "tone": "accent.primary" if read_only else "accent.warning",
    }


class DatabaseView(ctk.CTkFrame):
    """Database operations view with safety-first messaging."""

    def __init__(self, master, db_path: str, read_only: bool):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        summary = build_database_summary(db_path, read_only)

        title = ctk.CTkLabel(
            self,
            text="Database",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        badge = StatusBadge(self, text=summary["badge"], tone=summary["tone"])
        badge.grid(row=0, column=1, sticky="e")

        subtitle = ctk.CTkLabel(
            self,
            text="SQLite queries with explicit safety defaults",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 20))

        panel = PanelCard(self)
        panel.grid(row=2, column=0, columnspan=2, sticky="ew")

        label = ctk.CTkLabel(
            panel,
            text="Selected Database",
            text_color=get_color_token("text.primary"),
            font=get_font_token("body_medium"),
        )
        label.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))

        value = ctk.CTkLabel(
            panel,
            text=summary["path"],
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
            justify="left",
            wraplength=800,
        )
        value.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))
