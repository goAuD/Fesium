"""A label that renders at whatever width its cell gives it.

A Tk label reports the width its text needs, and a *wrapped* label reports its
``wraplength``. Either way the geometry manager honours that request, so a
label inside a grid cell can push its container wider - and a wrapped one is a
ratchet, demanding back whatever width it was last given. That defeats a
uniform column layout and, when the grid pushes back, shows up as a panel that
visibly shimmers.

The cure has two halves, and both are required:

1. The inner ``tkinter.Label`` asks for one character of width, so it stops
   dictating anything.
2. That same inner label is stretched horizontally inside its ``CTkLabel``
   frame, and the frame is stretched inside *its* cell.

Half two is the one that is easy to miss. ``CTkLabel._create_grid`` grids the
inner label with a sticky derived from ``anchor`` - ``anchor="w"`` becomes
``sticky="w"`` - so a frame 950px wide happily contains a 9px label and the
text renders one character wide. Doing only half one made every tile title and
paragraph in the app collapse. This class therefore enforces both halves
itself rather than leaving either to a caller: ``grid`` and ``pack`` are
overridden to add the horizontal stretch to whatever the caller asked for.

``_create_grid`` runs on construction, on a scaling change, and from
``configure`` for ``corner_radius`` and ``anchor`` only - notably *not* for
``wraplength``, ``text`` or ``font``. Reasserting from there is enough because
nothing else resets the inner label's width, but that is a fact about
CustomTkinter 5.2.2 rather than a guarantee, which is why
``tests/unit/ui/test_width_agnostic_label.py`` checks the end state.
"""

from tkinter import font as tkfont

import customtkinter as ctk

ELLIPSIS = "…"


def describe_font(font) -> tuple[str, int, str]:
    """Normalise a CTk font, which is a tuple here and a CTkFont there.

    ``cget("font")`` answers with whatever was passed in: the theme tokens are
    tuples, but a label built without an explicit font gets a ``CTkFont``, and
    unpacking that as a tuple raises.
    """
    if isinstance(font, (tuple, list)):
        family, size, *rest = font
        return family, size, ("bold" if "bold" in rest else "normal")
    return font.cget("family"), font.cget("size"), font.cget("weight")


def with_horizontal_stretch(sticky: str) -> str:
    """Add ``e`` and ``w`` to a sticky, keeping any vertical component.

    Replacing the sticky outright would silently drop ``n``/``s`` and quietly
    re-align the text, so the two are composed instead.
    """
    return "".join(sorted(set(sticky.lower()) | {"e", "w"}))


class WidthAgnosticLabel(ctk.CTkLabel):
    """CTkLabel that neither demands width nor collapses when denied it.

    ``elide=True`` replaces the tail of the text with an ellipsis when it does
    not fit, so a cut is visible rather than silent. Off by default: a wrapped
    label breaks across lines instead, and only single-line labels need it.
    """

    def __init__(self, master, *, elide: bool = False, **kwargs):
        self._elide = elide
        self._full_text = kwargs.get("text", "")
        super().__init__(master, **kwargs)
        if elide:
            self.bind("<Configure>", self._apply_elision, add="+")

    # -- half one and half two, reasserted whenever CustomTkinter regrids -----

    def _create_grid(self):
        super()._create_grid()
        inner = self._label
        inner.configure(width=1)
        anchor = self._anchor if self._anchor != "center" else ""
        inner.grid_configure(sticky=with_horizontal_stretch(anchor))

    # -- the cell has to stretch too, so do not leave that to the caller -----

    def grid(self, **kwargs):
        kwargs["sticky"] = with_horizontal_stretch(kwargs.get("sticky", ""))
        super().grid(**kwargs)

    def pack(self, **kwargs):
        fill = kwargs.get("fill", "none")
        kwargs["fill"] = "both" if fill in ("y", "both") else "x"
        super().pack(**kwargs)

    # -- optional visible truncation ----------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "text" in kwargs:
            self._full_text = kwargs["text"]
        super().configure(require_redraw=require_redraw, **kwargs)
        if self._elide:
            self._apply_elision()

    def _measure(self, text: str) -> int:
        family, size, weight = describe_font(self.cget("font"))
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        # Tk reads a positive font size as points and a negative one as pixels,
        # and CustomTkinter renders the negative form.
        rendered = -abs(round(size * scaling))
        return tkfont.Font(family=family, size=rendered, weight=weight).measure(text)

    def _apply_elision(self, _event=None) -> None:
        available = self._label.winfo_width()
        if available <= 1:
            return

        wanted = elide_to_width(self._full_text, available, self._measure)
        if wanted != self._label.cget("text"):
            self._label.configure(text=wanted)


def elide_to_width(text: str, available: int, measure) -> str:
    """Longest prefix of ``text`` that fits, with an ellipsis when cut."""
    if not text or measure(text) <= available:
        return text

    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if measure(text[:middle].rstrip() + ELLIPSIS) <= available:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + ELLIPSIS if low else ELLIPSIS
