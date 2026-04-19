import sys
import tkinter as tk
from pathlib import Path


ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"


def get_window_icon_paths():
    return {
        "png": ICON_DIR / "fesium-orbit-256.png",
        "ico": ICON_DIR / "fesium-orbit.ico",
    }


def apply_window_icon(window) -> bool:
    paths = get_window_icon_paths()
    png_path = paths["png"]
    ico_path = paths["ico"]

    if not png_path.exists():
        return False

    image = tk.PhotoImage(file=str(png_path))
    window._fesium_icon_image = image
    window.iconphoto(True, image)

    if sys.platform == "win32" and ico_path.exists():
        try:
            window.iconbitmap(default=str(ico_path))
        except Exception:
            pass

    return True
