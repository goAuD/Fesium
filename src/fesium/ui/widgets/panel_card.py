import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


def resolve_panel_surface(variant: str) -> dict[str, str | None]:
    variants = {
        "default": {"outer_fg": "bg.panel", "inner_fg": None},
        "inset": {"outer_fg": "bg.panel", "inner_fg": "bg.panel_alt"},
        "inset_strong": {"outer_fg": "bg.panel", "inner_fg": "bg.app"},
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
            fg_color=get_color_token(surface["outer_fg"]),
            border_color=get_color_token("border.default"),
            border_width=1,
            corner_radius=16,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.content_frame: ctk.CTkFrame = self

        inner_fg = surface["inner_fg"]
        if inner_fg is not None:
            self.inner_frame = ctk.CTkFrame(
                self,
                fg_color=get_color_token(inner_fg),
                corner_radius=14,
                border_width=0,
            )
            self.inner_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.inner_frame.grid_columnconfigure(0, weight=1)
            self.content_frame = self.inner_frame
