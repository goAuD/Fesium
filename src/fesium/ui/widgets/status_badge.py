import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_shape_token
from fesium.ui.theme.tokens import TEXT_CENTRING_OFFSET

BADGE_FONT = ("Atkinson Hyperlegible", 12, "bold")

# Vertical centring of the text depends on the bundled face, not on this
# widget, so it is decided once in the theme.


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
            corner_radius=get_shape_token("badge.radius"),
            padx=10,
            pady=3,
            anchor="center",
            **kwargs,
        )
        self._label.grid_configure(pady=(0, TEXT_CENTRING_OFFSET))
