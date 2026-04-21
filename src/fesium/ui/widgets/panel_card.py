import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


def resolve_panel_surface(variant: str) -> dict[str, str | int]:
    variants = {
        "default": {
            "fg_color": "bg.panel",
            "border_color": "border.default",
            "border_width": 1,
        },
        "inset": {
            "fg_color": "bg.panel_alt",
            "border_color": "border.default",
            "border_width": 1,
        },
        "inset_strong": {
            "fg_color": "bg.app",
            "border_color": "border.soft",
            "border_width": 1,
        },
    }
    try:
        return variants[variant]
    except KeyError as exc:
        raise ValueError(f"Unknown panel surface variant: {variant}") from exc


class PanelCard(ctk.CTkFrame):
    """Base panel surface used for cards in the Graphite Grid UI."""

    def __init__(self, master, *, surface_variant: str = "default", **kwargs):
        surface = resolve_panel_surface(surface_variant)
        super().__init__(
            master,
            fg_color=get_color_token(surface["fg_color"]),
            border_color=get_color_token(surface["border_color"]),
            border_width=surface["border_width"],
            corner_radius=16,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.content_frame = self
