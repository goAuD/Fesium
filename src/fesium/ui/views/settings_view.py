import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard


def build_settings_rows(config_data: dict):
    return [
        {"label": "Default Port", "value": str(config_data.get("port", 8000))},
        {"label": "Last Active View", "value": config_data.get("active_view", "overview")},
    ]


class SettingsView(ctk.CTkFrame):
    """Application settings summary view."""

    def __init__(self, master, config_data: dict):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Settings",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Preferences and defaults",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 20))

        panel = PanelCard(self)
        panel.grid(row=2, column=0, sticky="ew")

        rows = build_settings_rows(config_data)
        for row_index, row in enumerate(rows):
            label = ctk.CTkLabel(
                panel,
                text=row["label"],
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=row_index * 2, column=0, sticky="w", padx=16, pady=(16 if row_index == 0 else 10, 4))

            value = ctk.CTkLabel(
                panel,
                text=row["value"],
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
            )
            value.grid(
                row=row_index * 2 + 1,
                column=0,
                sticky="w",
                padx=16,
                pady=(0, 4 if row_index < len(rows) - 1 else 16),
            )
