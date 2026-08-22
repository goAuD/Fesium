from tkinter import font as tkfont

import customtkinter as ctk

from fesium.ui.theme.styles import get_button_style, resolve_button_style
from fesium.ui.theme.tokens import TEXT_CENTRING_OFFSET
from fesium.ui.widgets.icon import DEFAULT_ICON_SIZE, get_icon

# Floor for the width, so a one-word button still reads as a button and stays a
# comfortable target. Kept modest deliberately: at 150 it inflated Start, Stop
# and Restart far past their labels and pushed the Server control row onto a
# second line at window widths where it would otherwise have fitted.
MIN_BUTTON_WIDTH = 110

# Breathing room either side of the label.
#
# CustomTkinter derives its horizontal padding from
# ``max(corner_radius, border_width + 1, border_spacing)``, so squaring the
# corners dropped it from 10px to 2px and the text ran into the border. Raising
# border_spacing would fix that but also pads vertically, making every button
# taller, so the width is computed from the measured text instead.
BUTTON_TEXT_PADDING = 16

# Vertical centring of the text depends on the bundled face, not on this
# widget, so it is decided once in the theme. See TEXT_CENTRING_OFFSET there.


def measure_button_width(master, text: str, font, *, with_icon: bool = False) -> int:
    """Width that fits the label plus padding, never below the shared minimum.

    Mirrors what CustomTkinter actually renders. It passes fonts to Tk with a
    *negative* size, which Tk reads as pixels; a positive size means points, and
    at 96dpi that is about 30% larger - measuring the wrong one padded a button
    by 39px instead of 16. The result is divided back out of the display scaling
    because ``width`` is in unscaled CTk units.
    """
    family, size, *rest = font
    weight = "bold" if "bold" in rest else "normal"
    scaling = ctk.ScalingTracker.get_widget_scaling(master)
    rendered_size = -abs(round(size * scaling))
    text_width = tkfont.Font(family=family, size=rendered_size, weight=weight).measure(text) / scaling
    icon_width = DEFAULT_ICON_SIZE + 6 if with_icon else 0
    return max(MIN_BUTTON_WIDTH, round(text_width + icon_width + 2 * BUTTON_TEXT_PADDING))


class Button(ctk.CTkButton):
    """The one button in Fesium.

    Views used to build ``CTkButton`` by hand and spread ``get_button_style``
    over the call, which meant every view repeated the enabled/disabled dance
    and picked its own width. Both now live here.

    ``variant`` is one of ``primary``, ``secondary``, ``danger``,
    ``danger_secondary`` or ``nav``. Use ``set_enabled`` rather than
    ``configure(state=...)``: the state and the colours have to change
    together, or a disabled button keeps the fill of an enabled one.
    """

    def __init__(
        self,
        master,
        text: str,
        *,
        variant: str = "secondary",
        enabled: bool = True,
        active: bool = False,
        icon: str | None = None,
        command=None,
        **kwargs,
    ):
        self._variant = variant
        self._active = active
        self._enabled = enabled
        self._icon = icon
        style = get_button_style(variant, active=active, enabled=enabled)
        kwargs.setdefault("width", measure_button_width(master, text, style["font"], with_icon=bool(icon)))
        if icon:
            kwargs.setdefault("image", get_icon(icon, tone=self._icon_tone()))
            kwargs.setdefault("compound", "left")
        super().__init__(
            master,
            text=text,
            state="normal" if enabled else "disabled",
            command=command,
            **style,
            **kwargs,
        )

    def _icon_tone(self) -> str:
        """Match the icon to the label, so the pair reads as one element.

        resolve_button_style returns token names rather than resolved hex, which
        is exactly what get_icon wants.
        """
        return resolve_button_style(self._variant, active=self._active, enabled=self._enabled)["text_color"]

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._restyle()

    def set_active(self, active: bool) -> None:
        """Only meaningful for the ``nav`` variant, which marks the current view."""
        self._active = active
        self._restyle()

    def _create_grid(self):
        """Re-apply the label nudge whenever CustomTkinter rebuilds the grid.

        ``_create_grid`` runs again on configure and on a scaling change, and a
        fresh ``grid()`` call resets padding, so the correction has to live here
        rather than being applied once at construction.
        """
        super()._create_grid()
        if getattr(self, "_text_label", None) is not None:
            self._text_label.grid_configure(pady=(0, TEXT_CENTRING_OFFSET))

    def _restyle(self) -> None:
        style = get_button_style(self._variant, active=self._active, enabled=self._enabled)
        self.configure(state="normal" if self._enabled else "disabled", **style)
        if self._icon:
            self.configure(image=get_icon(self._icon, tone=self._icon_tone()))
