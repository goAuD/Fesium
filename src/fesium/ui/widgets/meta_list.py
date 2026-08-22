import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.body_text import BodyText
from fesium.ui.widgets.width_agnostic_label import WidthAgnosticLabel

LABEL_COLUMN_WIDTH = 150
LABEL_GUTTER = 16
# The label column never takes more than this share of the list. A fixed 150px
# reserve is fine in a half-width tile and ruinous in a quarter-width one: it
# left a Windows path 131px to render 157px in.
MAX_LABEL_SHARE = 0.42
MIN_LABEL_COLUMN_WIDTH = 64


def resolve_label_column_width(
    available_width: float,
    *,
    preferred: int = LABEL_COLUMN_WIDTH,
    minimum: int = MIN_LABEL_COLUMN_WIDTH,
) -> int:
    """How much of the row the labels may reserve, given the width on offer."""
    if available_width <= 0:
        return preferred
    return max(minimum, min(preferred, int(available_width * MAX_LABEL_SHARE)))


class MetaList(ctk.CTkFrame):
    """Compact label/value rows, one line each.

    Replaces the label-above-value pattern the views used to repeat. That
    pattern costs two lines per fact: the Server view spent 580px presenting
    seven of them. Two columns fit the same content in roughly a third of the
    height, and the labels line up into a readable edge.

    Both columns are width-agnostic. A label that insisted on its natural width
    could squeeze the value beside it to nothing in a narrow tile, so the labels
    elide instead and the reserve yields as the list gets narrower.
    """

    def __init__(self, master, rows: tuple[tuple[str, str], ...], *, row_gap: int = 10):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=0, minsize=LABEL_COLUMN_WIDTH)
        self.grid_columnconfigure(1, weight=1)

        for index, (label, value) in enumerate(rows):
            pady = (0 if index == 0 else row_gap, 0)

            label_widget = WidthAgnosticLabel(
                self,
                text=label,
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                anchor="nw",
                elide=True,
            )
            label_widget.grid(row=index, column=0, sticky="nw", pady=pady, padx=(0, LABEL_GUTTER))

            value_widget = BodyText(self, value, tone="text.primary")
            value_widget.grid(row=index, column=1, sticky="ew", pady=pady)

        self.bind("<Configure>", self._resize_label_column)

    def _resize_label_column(self, event) -> None:
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        target = resolve_label_column_width(event.width / scaling - LABEL_GUTTER)
        if target != self.grid_columnconfigure(0).get("minsize"):
            self.grid_columnconfigure(0, minsize=target)
