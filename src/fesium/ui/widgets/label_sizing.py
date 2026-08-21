"""Stop a label from dictating the width of everything around it.

A Tk label reports the width its text needs, and a *wrapped* label reports its
``wraplength``. Either way the geometry manager honours that request, so a
label inside a grid cell can push its container wider - and a wrapped one is a
ratchet, demanding back whatever width it was last given. That defeats a
uniform column layout and, when the grid pushes back, shows up as a panel that
visibly shimmers.

The cure is to make the label ask for one character and let its cell decide.

    CALLERS MUST GRID THE LABEL WITH A STICKY THAT INCLUDES BOTH "e" AND "w",
    IN A COLUMN THAT HAS WEIGHT.

Without that the cell hands back the one character that was asked for, Tk clips
the text to fit, and the label renders about 8px wide - which is how every tile
title and meta once vanished from the app at once.
"""


def detach_width_request(ctk_label) -> None:
    """Ask for one character of width. The cell has to supply the rest."""
    ctk_label._label.configure(width=1)
