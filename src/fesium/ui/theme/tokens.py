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

FONT_TOKENS = {
    "heading": ("Sora", 28, "bold"),
    "section_heading": ("Sora", 18, "bold"),
    # Tile titles are deliberately small and quiet. In a bento layout the size
    # of a tile says how important it is, so the heading does not have to
    # shout - and when every heading shouts, none of them carry meaning.
    "tile_title": ("Sora", 12, "bold"),
    # The one figure a tile is about: a row count, a port, a status word.
    "metric": ("Sora", 22, "bold"),
    "body": ("IBM Plex Sans", 16),
    "body_medium": ("IBM Plex Sans", 16, "bold"),
    # Right-hand side of a tile header: counts, units, short qualifiers.
    "meta": ("IBM Plex Sans", 13),
    "mono": ("JetBrains Mono", 14),
}
