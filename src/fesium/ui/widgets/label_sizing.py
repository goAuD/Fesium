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
2. That same inner label is gridded to stretch inside its ``CTkLabel`` frame.

Half two is the one that is easy to miss. ``CTkLabel._create_grid`` grids the
inner label with a sticky derived from ``anchor`` - ``anchor="w"`` becomes
``sticky="w"`` - so a frame 950px wide happily contains a 9px label, and the
text renders one character wide. Doing only half one made every tile title and
paragraph in the app collapse. CustomTkinter rebuilds that grid on configure
and on a scaling change, so the override has to reassert it every time.

Callers still have to grid the ``CTkLabel`` itself with a sticky containing
``e`` and ``w``, in a column that has weight. Nothing here can supply width
that its own cell never gave it.
"""

import customtkinter as ctk


class WidthAgnosticLabel(ctk.CTkLabel):
    """CTkLabel that neither demands width nor collapses when denied it."""

    def _create_grid(self):
        super()._create_grid()
        inner = getattr(self, "_label", None)
        if inner is None:
            return
        # One character wide as a request, full cell width in practice.
        inner.configure(width=1)
        inner.grid_configure(sticky="ew")
