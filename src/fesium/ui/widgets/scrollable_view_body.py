import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


def resolve_scrollable_view_body_style() -> dict[str, str]:
    return {
        "fg_color": "transparent",
        "scrollbar_fg": "bg.app",
        "scrollbar_button": "bg.panel",
        "scrollbar_button_hover": "bg.panel_alt",
    }


class ScrollableViewBody(ctk.CTkScrollableFrame):
    """Shared scrollable content body for tall desktop views."""

    def __init__(self, master, **kwargs):
        style = resolve_scrollable_view_body_style()
        super().__init__(
            master,
            fg_color=style["fg_color"],
            scrollbar_fg_color=get_color_token(style["scrollbar_fg"]),
            scrollbar_button_color=get_color_token(style["scrollbar_button"]),
            scrollbar_button_hover_color=get_color_token(style["scrollbar_button_hover"]),
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
