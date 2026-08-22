COLOR_TOKENS = {
    "bg.app": "#121419",
    "bg.sidebar": "#171a21",
    "bg.panel": "#181d25",
    "bg.panel_alt": "#151a22",
    "bg.panel_hover": "#1d222c",
    "border.default": "#2b3440",
    "border.soft": "#29313d",
    "text.primary": "#eef3f7",
    "text.secondary": "#8f9aa8",
    "accent.primary": "#5DA9B3",
    "accent.primary_hover": "#6EBAC4",
    "accent.primary_soft": "#1e2d32",
    "accent.success": "#7EB89B",
    "accent.warning": "#D1A168",
    "accent.danger": "#CC6D6D",
    "accent.danger_hover": "#D97E7E",
    "accent.danger_soft": "#2e1e1e",
}

# Corner geometry, in one place because it is a single design decision.
#
# CustomTkinter draws a rounded corner as an anti-aliased circle glyph and the
# straight edges as hard-edged rectangles, on the same canvas. Where a radius
# meets a border the two never line up, and the corner reads as doubled. Every
# pairing below therefore avoids a border or avoids a radius, never both.
SHAPE_TOKENS = {
    "tile.radius": 0,
    "tile.border": 1,
    "button.radius": 0,
    "button.border": 1,
    "input.radius": 0,
    "input.border": 1,
    # A badge is a CTkLabel, which cannot take a border at all, so the capsule
    # draws one clean arc and the pill shape survives any decision above.
    "badge.radius": 999,
}

# One family for everything the app writes, plus a mono for code.
#
# Atkinson Hyperlegible was drawn by the Braille Institute specifically so that
# confusable characters stay apart, and it is the only face considered here with
# a dotted zero - which matters in a tool whose screens are ports, process ids,
# row counts and paths. Measured at 16px against Sora, IBM Plex Sans, Source
# Sans 3 and Public Sans, judged on the worst confusable pair rather than the
# average, because a reader is tripped by the one pair a face gets wrong.
#
# It replaced Sora, whose lowercase l and digit 1 measured 0.10 apart on that
# scale - the worst pair of any candidate - and which was being asked to set
# 12px tile titles, work a display face was never drawn for.
#
# Size and weight carry the hierarchy here, which is what the bento layout
# already does. A separate display family would argue with that.
FONT_TOKENS = {
    "heading": ("Atkinson Hyperlegible", 28, "bold"),
    "section_heading": ("Atkinson Hyperlegible", 18, "bold"),
    # Tile titles are deliberately small and quiet. In a bento layout the size
    # of a tile says how important it is, so the heading does not have to
    # shout - and when every heading shouts, none of them carry meaning.
    "tile_title": ("Atkinson Hyperlegible", 12, "bold"),
    # The one figure a tile is about: a row count, a port, a status word.
    "metric": ("Atkinson Hyperlegible", 22, "bold"),
    "body": ("Atkinson Hyperlegible", 16),
    "body_medium": ("Atkinson Hyperlegible", 16, "bold"),
    # Right-hand side of a tile header: counts, units, short qualifiers.
    "meta": ("Atkinson Hyperlegible", 13),
    "mono": ("JetBrains Mono", 14),
}
