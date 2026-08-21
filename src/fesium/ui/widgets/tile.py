import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token, get_shape_token

TILE_PADDING = 16

# The meta slot is for a short qualifier - a count, a unit, a status word. It
# is a single-line label, so it demands its full text width and a long string
# there stretches the tile and squeezes whatever shares its row. Truncating
# keeps a mistake visible instead of letting it wreck the layout.
MAX_META_CHARS = 40


def truncate_meta(meta: str, limit: int = MAX_META_CHARS) -> str:
    return meta if len(meta) <= limit else meta[: limit - 1].rstrip() + "…"


class Tile(ctk.CTkFrame):
    """One tile: a quiet title, optional right-hand meta, and a body to fill.

    Two things matter about it:

    * The title is small, uppercase and secondary-coloured. Tile size carries
      the hierarchy, so the accent is free to mean something again - active
      state, the primary action, live status.
    * ``body`` stretches. Nothing inside a tile should carry a fixed pixel
      height; that is what left the gaps in the old stacked panels.
    """

    def __init__(
        self,
        master,
        title: str,
        *,
        meta: str = "",
        meta_tone: str = "text.secondary",
        surface: str = "bg.panel",
        padding: int = TILE_PADDING,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=get_color_token(surface),
            border_color=get_color_token("border.default"),
            border_width=get_shape_token("tile.border"),
            corner_radius=get_shape_token("tile.radius"),
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=padding, pady=(padding, 10))
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text=title.upper(),
            text_color=get_color_token("text.secondary"),
            font=get_font_token("tile_title"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.meta_label = ctk.CTkLabel(
            header,
            text=truncate_meta(meta),
            text_color=get_color_token(meta_tone),
            font=get_font_token("meta"),
            anchor="e",
        )
        self.meta_label.grid(row=0, column=1, sticky="e")

        # Header labels are decoration, not content: a longer tile name must not
        # make its tile wider than the grid share it was given, or two tiles
        # meant to be equal come out 43px apart. Width is the grid's decision;
        # these ask for one character and take what the cell gives them.
        for label in (self.title_label, self.meta_label):
            label._label.configure(width=1)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=padding, pady=(0, padding))
        self.body.grid_columnconfigure(0, weight=1)

    def set_title(self, title: str) -> None:
        self.title_label.configure(text=title.upper())

    def set_meta(self, meta: str, tone: str = "text.secondary") -> None:
        self.meta_label.configure(text=truncate_meta(meta), text_color=get_color_token(tone))
