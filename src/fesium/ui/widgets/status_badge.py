import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


BADGE_FONT = ("IBM Plex Sans", 12, "bold")


class StatusBadge(ctk.CTkLabel):
    """Small capsule label for status indicators."""

    def __init__(self, master, text: str, tone: str = "accent.primary", **kwargs):
        super().__init__(
            master,
            text=text,
            text_color=get_color_token("bg.app"),
            fg_color=get_color_token(tone),
            font=BADGE_FONT,
            height=24,
            corner_radius=999,
            padx=10,
            pady=3,
            anchor="center",
            **kwargs,
        )
