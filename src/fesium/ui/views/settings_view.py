import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.panel_card import PanelCard
from fesium.ui.widgets.scrollable_view_body import ScrollableViewBody


def build_settings_placeholder(config_data: dict) -> dict[str, str]:
    return {
        "title": "No in-app settings yet",
        "body": (
            "This page stays intentionally minimal until Fesium has real app preferences to expose. "
            "The old summary tables were removed so this screen does not pretend to be configurable."
        ),
        "footnote": (
            "Current defaults remain automatic: the last valid workspace can be restored, "
            "server startup stays manual, and SQLite opens in read-only mode each launch."
        ),
    }


class SettingsView(ctk.CTkFrame):
    """Placeholder view for future application preferences."""

    def __init__(self, master, config_data: dict):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        placeholder = build_settings_placeholder(config_data)

        title = ctk.CTkLabel(
            self,
            text="Settings",
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Reserved for future app preferences",
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
        panel_content.grid_columnconfigure(0, weight=1)

        panel_title = ctk.CTkLabel(
            panel_content,
            text=placeholder["title"],
            text_color=get_color_token("accent.primary"),
            font=get_font_token("section_heading"),
        )
        panel_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        body_label = ctk.CTkLabel(
            panel_content,
            text=placeholder["body"],
            text_color=get_color_token("text.primary"),
            font=get_font_token("body"),
            justify="left",
            wraplength=860,
        )
        body_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        footnote_label = ctk.CTkLabel(
            panel_content,
            text=placeholder["footnote"],
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
            justify="left",
            wraplength=860,
        )
        footnote_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))
