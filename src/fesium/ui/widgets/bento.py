import customtkinter as ctk

# Twelve divides by 2, 3, 4 and 6, so the common splits all land on whole
# columns without a leftover.
BENTO_COLUMNS = 12
BENTO_GUTTER = 14


def resolve_tile_padding(*, row: int, column: int, gutter: int = BENTO_GUTTER) -> dict[str, tuple[int, int]]:
    """Give each gutter to the tile that follows it.

    A tile pads only its left and top edge, and only when something precedes
    it. Two adjacent tiles are then exactly one gutter apart, and the grid sits
    flush against the view's own padding on all four sides - no double gap in
    the middle, no stray margin at the edges.
    """
    return {
        "padx": (0 if column == 0 else gutter, 0),
        "pady": (0 if row == 0 else gutter, 0),
    }


class BentoGrid(ctk.CTkFrame):
    """A fixed-column grid that tiles claim space in by span.

    The point of the layout is that size carries the hierarchy: a tile that
    matters spans more columns or gets more row weight, so it does not need a
    louder heading to say so. Columns share a `uniform` group, which keeps the
    column width independent of the content inside any one tile - otherwise a
    long file path would quietly widen its column and knock the grid askew.
    """

    def __init__(self, master, *, columns: int = BENTO_COLUMNS, gutter: int = BENTO_GUTTER, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columns = columns
        self.gutter = gutter
        for column in range(columns):
            self.grid_columnconfigure(column, weight=1, uniform="bento")

    def place_tile(self, tile, *, row: int, column: int, span: int, rowspan: int = 1, row_weight: int = 0):
        """Put a tile on the grid. ``row_weight`` decides who absorbs spare height."""
        if span < 1 or column < 0 or column + span > self.columns:
            raise ValueError(
                f"Tile at column {column} spanning {span} does not fit {self.columns} columns"
            )

        tile.grid(
            row=row,
            column=column,
            columnspan=span,
            rowspan=rowspan,
            sticky="nsew",
            **resolve_tile_padding(row=row, column=column, gutter=self.gutter),
        )
        if row_weight:
            self.grid_rowconfigure(row, weight=row_weight)
        return tile
