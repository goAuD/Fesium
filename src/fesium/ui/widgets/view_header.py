import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.status_badge import StatusBadge

# Space between the header and the grid below it.
HEADER_GAP = 20


class ViewHeader(ctk.CTkFrame):
    """Title, subtitle and optional badges, identical on every view.

    Every view used to build its own header, and they drifted: content started
    up to 6px apart horizontally and 8px apart vertically depending on which
    view you were looking at, which read as a jump when switching pages. Grid
    this at row 0 of a view and the body at row 1, and every page lines up.
    """

    def __init__(self, master, title: str, subtitle: str, *, badges: tuple[tuple[str, str], ...] = ()):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=get_color_token("text.primary"),
            font=get_font_token("heading"),
            anchor="w",
        )
        title_label.grid(row=0, column=0, sticky="w")

        if badges:
            badge_row = ctk.CTkFrame(self, fg_color="transparent")
            badge_row.grid(row=0, column=1, sticky="e")
            for index, (text, tone) in enumerate(badges):
                StatusBadge(badge_row, text=text, tone=tone).pack(
                    side="left", padx=(0 if index == 0 else 8, 0)
                )

        subtitle_label = ctk.CTkLabel(
            self,
            text=subtitle,
            text_color=get_color_token("text.secondary"),
            font=get_font_token("body"),
            anchor="w",
        )
        subtitle_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
