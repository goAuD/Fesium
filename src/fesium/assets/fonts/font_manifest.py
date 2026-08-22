from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent

# Roles map to files, not families, because the loader registers whatever these
# point at. Atkinson ships as static Regular and Bold rather than one variable
# file, so both faces have to appear here or Windows only ever sees the one.
FONT_FILES = {
    "heading": FONT_DIR / "AtkinsonHyperlegible-Bold.ttf",
    "body": FONT_DIR / "AtkinsonHyperlegible-Regular.ttf",
    "body_medium": FONT_DIR / "AtkinsonHyperlegible-Bold.ttf",
    "mono": FONT_DIR / "JetBrainsMono-Regular.ttf",
}
