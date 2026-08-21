import customtkinter as ctk

from fesium.ui.theme.font_loader import register_bundled_fonts
from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS, SHAPE_TOKENS


def apply_graphite_grid_theme() -> None:
    """Apply the base CustomTkinter theme primitives for Fesium."""
    register_bundled_fonts()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")


def get_color_token(name: str) -> str:
    return COLOR_TOKENS[name]


def get_font_token(name: str):
    return FONT_TOKENS[name]


# CustomTkinter only swaps the text colour on a disabled button and leaves the
# fill alone. A disabled `primary` therefore renders text.secondary on top of a
# full-strength accent - roughly 1.05:1 contrast, which is unreadable, and it
# does not look disabled either. Swapping the surface as well fixes both.
DISABLED_OVERRIDES = {
    "fg_color": "bg.panel_alt",
    "hover_color": "bg.panel_alt",
    "text_color": "text.secondary",
    "border_color": "border.soft",
}


def get_shape_token(name: str):
    return SHAPE_TOKENS[name]


def resolve_button_style(variant: str, *, active: bool = False, enabled: bool = True) -> dict[str, object]:
    button_base = {
        "height": 38,
        "corner_radius": SHAPE_TOKENS["button.radius"],
        "font": FONT_TOKENS["body_medium"],
    }
    styles = {
        "primary": {
            **button_base,
            "fg_color": "accent.primary",
            "hover_color": "accent.primary_hover",
            "text_color": "bg.app",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.primary",
            "border_width": SHAPE_TOKENS["button.border"],
        },
        "secondary": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "accent.primary_soft",
            "text_color": "accent.primary",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.primary",
            "border_width": SHAPE_TOKENS["button.border"],
        },
        "danger": {
            **button_base,
            "fg_color": "accent.danger",
            "hover_color": "accent.danger_hover",
            "text_color": "bg.app",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.danger",
            "border_width": SHAPE_TOKENS["button.border"],
        },
        "danger_secondary": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "accent.danger_soft",
            "text_color": "accent.danger",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.danger",
            "border_width": SHAPE_TOKENS["button.border"],
        },
        # Nav rows carry no border. Six bordered boxes stacked in a column read
        # as six separate things; the sidebar is one surface with a marked row.
        "nav": {
            **button_base,
            "fg_color": "bg.sidebar",
            "hover_color": "bg.panel_hover",
            "text_color": "text.secondary",
            "text_color_disabled": "text.secondary",
            "border_color": "bg.sidebar",
            "border_width": 0,
        },
        "nav_active": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "bg.panel",
            # The accent earns its keep here: this is the state it exists to
            # mark, and it carries the icon with it.
            "text_color": "accent.primary",
            "text_color_disabled": "text.secondary",
            "border_color": "bg.panel",
            "border_width": 0,
        },
    }

    resolved_key = "nav_active" if variant == "nav" and active else variant
    try:
        style = styles[resolved_key]
    except KeyError as exc:
        raise ValueError(f"Unknown button style variant: {variant}") from exc

    return style if enabled else {**style, **DISABLED_OVERRIDES}


def get_button_style(variant: str, *, active: bool = False, enabled: bool = True) -> dict[str, object]:
    style = resolve_button_style(variant, active=active, enabled=enabled)
    resolved: dict[str, object] = {}
    for key, value in style.items():
        if isinstance(value, tuple):
            resolved[key] = value
        elif isinstance(value, str) and value in COLOR_TOKENS:
            resolved[key] = get_color_token(value)
        else:
            resolved[key] = value
    return resolved
