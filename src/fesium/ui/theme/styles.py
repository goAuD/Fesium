import customtkinter as ctk

from fesium.ui.theme.font_loader import register_bundled_fonts
from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS


def apply_graphite_grid_theme() -> None:
    """Apply the base CustomTkinter theme primitives for Fesium."""
    register_bundled_fonts()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")


def get_color_token(name: str) -> str:
    return COLOR_TOKENS[name]


def get_font_token(name: str):
    return FONT_TOKENS[name]


def resolve_button_style(variant: str, *, active: bool = False) -> dict[str, object]:
    button_base = {
        "height": 38,
        "corner_radius": 10,
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
            "border_width": 1,
        },
        "secondary": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "accent.primary_soft",
            "text_color": "accent.primary",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.primary",
            "border_width": 1,
        },
        "danger": {
            **button_base,
            "fg_color": "accent.danger",
            "hover_color": "accent.danger_hover",
            "text_color": "bg.app",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.danger",
            "border_width": 1,
        },
        "danger_secondary": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "accent.danger_soft",
            "text_color": "accent.danger",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.danger",
            "border_width": 1,
        },
        "nav": {
            **button_base,
            "fg_color": "bg.panel",
            "hover_color": "bg.panel_hover",
            "text_color": "text.primary",
            "text_color_disabled": "text.secondary",
            "border_color": "border.soft",
            "border_width": 1,
        },
        "nav_active": {
            **button_base,
            "fg_color": "bg.panel_alt",
            "hover_color": "bg.panel_alt",
            "text_color": "text.primary",
            "text_color_disabled": "text.secondary",
            "border_color": "accent.primary",
            "border_width": 1,
        },
    }

    resolved_key = "nav_active" if variant == "nav" and active else variant
    try:
        return styles[resolved_key]
    except KeyError as exc:
        raise ValueError(f"Unknown button style variant: {variant}") from exc


def get_button_style(variant: str, *, active: bool = False) -> dict[str, object]:
    style = resolve_button_style(variant, active=active)
    resolved: dict[str, object] = {}
    for key, value in style.items():
        if isinstance(value, tuple):
            resolved[key] = value
        elif isinstance(value, str) and value in COLOR_TOKENS:
            resolved[key] = get_color_token(value)
        else:
            resolved[key] = value
    return resolved
