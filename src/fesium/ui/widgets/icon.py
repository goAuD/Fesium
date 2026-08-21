"""Bundled Lucide icons, tinted to theme colours.

The PNGs ship white on transparent and are recoloured here, so one file serves
every state an icon appears in - a nav item is secondary when idle and accent
when active, from the same source.

Regenerate the PNGs with ``python scripts/build_icons.py`` after changing an
SVG source. Nothing fetches or rasterises at runtime; Fesium stays offline.
"""

from pathlib import Path

import customtkinter as ctk
from PIL import Image

from fesium.ui.theme.styles import get_color_token

ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons" / "lucide"

DEFAULT_ICON_SIZE = 20

# Tk drops an image as soon as nothing references it, and the widget displaying
# it does not count as a reference. This cache keeps every tinted variant alive
# for the life of the process.
_CACHE: dict[tuple[str, str, int], ctk.CTkImage] = {}


def available_icons() -> list[str]:
    return sorted(path.stem for path in ICON_DIR.glob("*.png") if not path.stem.endswith("@2x"))


def icon_source(name: str) -> Image.Image:
    """Load the 2x master for an icon. CTkImage scales it down to the size asked for."""
    path = ICON_DIR / f"{name}@2x.png"
    if not path.exists():
        raise FileNotFoundError(f"No bundled icon named {name!r}. Available: {', '.join(available_icons())}")
    return Image.open(path).convert("RGBA")


def tint(image: Image.Image, color: str) -> Image.Image:
    """Recolour a white-on-transparent icon, keeping its alpha as the shape."""
    hex_digits = color.lstrip("#")
    rgb = tuple(int(hex_digits[index : index + 2], 16) for index in (0, 2, 4))
    solid = Image.new("RGBA", image.size, (*rgb, 255))
    solid.putalpha(image.getchannel("A"))
    return solid


def get_icon(name: str, *, tone: str = "text.secondary", size: int = DEFAULT_ICON_SIZE) -> ctk.CTkImage:
    """Return a CTkImage of a bundled Lucide icon in the given theme colour."""
    key = (name, tone, size)
    if key not in _CACHE:
        tinted = tint(icon_source(name), get_color_token(tone))
        # Fesium renders dark only, but supplying both keeps the icon correct if
        # the appearance mode is ever switched.
        _CACHE[key] = ctk.CTkImage(light_image=tinted, dark_image=tinted, size=(size, size))
    return _CACHE[key]
