import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody


def build_environment_rows(status):
    return [
        {"label": "PHP", "value": status.summary},
        {"label": "Version", "value": status.php_version or "Unavailable"},
    ]


class EnvironmentView(ctk.CTkFrame):
    """Environment diagnostics view."""

    def __init__(self, master, status):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Environment",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Local toolchain diagnostics",
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 20))

        body = ScrollableViewBody(self)
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        panel = PanelCard(body, surface_variant="inset")
        panel.grid(row=0, column=0, sticky="ew")
        panel_content = panel.content_frame

        rows = build_environment_rows(status)
        for row_index, row in enumerate(rows):
            label = ctk.CTkLabel(
                panel_content,
                text=row["label"],
                text_color=get_color_token("text.primary"),
                font=get_font_token("body_medium"),
            )
            label.grid(row=row_index * 2, column=0, sticky="w", padx=16, pady=(16 if row_index == 0 else 10, 4))

            value = ctk.CTkLabel(
                panel_content,
                text=row["value"],
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                justify="left",
                wraplength=800,
            )
            value.grid(
                row=row_index * 2 + 1,
                column=0,
                sticky="w",
                padx=16,
                pady=(0, 4 if row_index < len(rows) - 1 else 16),
            )
