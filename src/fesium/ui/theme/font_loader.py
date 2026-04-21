import ctypes
import logging
import sys
from pathlib import Path

from fesium.assets.fonts.font_manifest import FONT_FILES


logger = logging.getLogger(__name__)

FR_PRIVATE = 0x10
_LOADED_FONTS: set[str] = set()


def register_bundled_fonts() -> None:
    """Best-effort registration of bundled fonts for the current process."""
    if sys.platform != "win32":
        return

    add_font = getattr(getattr(ctypes, "windll", None), "gdi32", None)
    if add_font is None or not hasattr(add_font, "AddFontResourceExW"):
        return

    add_font_resource = add_font.AddFontResourceExW
    unique_fonts = {str(Path(path).resolve()) for path in FONT_FILES.values()}
    for font_path in unique_fonts:
        if font_path in _LOADED_FONTS:
            continue

        loaded = add_font_resource(font_path, FR_PRIVATE, 0)
        if loaded:
            _LOADED_FONTS.add(font_path)
        else:
            logger.debug("Bundled font registration skipped for %s", font_path)
