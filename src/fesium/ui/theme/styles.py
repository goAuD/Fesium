import customtkinter as ctk

from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS


def apply_graphite_grid_theme() -> None:
    """Apply the base CustomTkinter theme primitives for Fesium."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")


def get_color_token(name: str) -> str:
    return COLOR_TOKENS[name]


def get_font_token(name: str):
    return FONT_TOKENS[name]
