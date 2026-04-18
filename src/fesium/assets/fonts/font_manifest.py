from pathlib import Path


FONT_DIR = Path(__file__).resolve().parent

FONT_FILES = {
    "heading": FONT_DIR / "Sora[wght].ttf",
    "body": FONT_DIR / "IBMPlexSans[wdth,wght].ttf",
    "body_medium": FONT_DIR / "IBMPlexSans[wdth,wght].ttf",
    "mono": FONT_DIR / "JetBrainsMono-Regular.ttf",
}
