import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.body_text import BodyText

LABEL_COLUMN_WIDTH = 150


class MetaList(ctk.CTkFrame):
    """Compact label/value rows, one line each.

    Replaces the label-above-value pattern the views used to repeat. That
    pattern costs two lines per fact: the Server view spent 580px presenting
    seven of them. Two columns fit the same content in roughly a third of the
    height, and the labels line up into a readable edge.
    """

    def __init__(self, master, rows: tuple[tuple[str, str], ...], *, row_gap: int = 10):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=0, minsize=LABEL_COLUMN_WIDTH)
        self.grid_columnconfigure(1, weight=1)

        for index, (label, value) in enumerate(rows):
            pady = (0 if index == 0 else row_gap, 0)

            label_widget = ctk.CTkLabel(
                self,
                text=label,
                text_color=get_color_token("text.secondary"),
                font=get_font_token("body"),
                anchor="nw",
            )
            label_widget.grid(row=index, column=0, sticky="nw", pady=pady, padx=(0, 16))

            value_widget = BodyText(self, value, tone="text.primary")
            value_widget.grid(row=index, column=1, sticky="ew", pady=pady)
