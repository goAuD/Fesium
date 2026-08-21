import tkinter

import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token, get_font_token
from fesium.ui.widgets.label_sizing import WidthAgnosticLabel

# Provisional wrap used before the widget has been given a real size.
MIN_WRAPLENGTH = 160
# Below this a wrap is meaningless, so stop shrinking rather than produce a
# column one character wide.
MIN_USABLE_WRAPLENGTH = 32


def resolve_wraplength(available_width: int, *, inner_padding: int = 0) -> int:
    """Return the wrap width a paragraph may use inside ``available_width``.

    Never wider than the space actually available: wrapping past the cell is
    exactly what pushes text outside its panel. The floor applies only before
    the first layout pass, when the widget has no width yet.
    """
    usable = int(available_width) - 2 * int(inner_padding)
    if usable <= 0:
        return MIN_WRAPLENGTH
    return max(MIN_USABLE_WRAPLENGTH, usable)


class BodyText(WidthAgnosticLabel):
    """Left-aligned paragraph label that wraps to the width it is actually given.

    ``CTkLabel`` takes ``wraplength`` in pixels, so a hardcoded value is only
    correct at one window size. When it exceeds the width grid hands the label,
    Tk still lays out full-width lines and the panel clips them - the start and
    end of every line disappear. Recomputing the wrap on every ``<Configure>``
    keeps paragraphs inside their panel at any window size.

    Grid this with ``sticky="ew"`` so the cell drives the width instead of the
    label sizing itself from its own text.
    """

    def __init__(self, master, text: str, *, tone: str = "text.primary", font: str = "body", **kwargs):
        super().__init__(
            master,
            text=text,
            text_color=get_color_token(tone),
            font=get_font_token(font),
            justify="left",
            anchor="w",
            wraplength=MIN_WRAPLENGTH,
            **kwargs,
        )
        # CTkLabel.bind() forwards to the inner canvas and tkinter.Label, whose
        # widths are not the cell width. Bind on the CTkLabel frame itself, and
        # add to - never replace - CustomTkinter's own <Configure> handler.
        tkinter.Frame.bind(self, "<Configure>", self._sync_wraplength, add="+")

    def _sync_wraplength(self, event) -> None:
        # event.width is in real pixels; wraplength is in unscaled CTk units.
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        target = resolve_wraplength(
            event.width / scaling,
            inner_padding=self.cget("corner_radius"),
        )
        if target != self.cget("wraplength"):
            self.configure(wraplength=target)
