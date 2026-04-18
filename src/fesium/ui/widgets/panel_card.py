import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


class PanelCard(ctk.CTkFrame):
    """Base panel surface used for cards in the Graphite Grid UI."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=get_color_token("bg.panel"),
            border_color=get_color_token("border.default"),
            border_width=1,
            corner_radius=16,
            **kwargs,
        )
