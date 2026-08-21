import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_shape_token

BADGE_FONT = ("IBM Plex Sans", 12, "bold")

# Tk centres a label on the font's line box, which reserves room above the caps
# for accents this text never uses, so the cap block lands a pixel low. Measured
# on a descender-free string, 2px of bottom padding brings it to 8px above and
# 8px below in a 24px capsule.
TEXT_CENTRING_OFFSET = 2


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
