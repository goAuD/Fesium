"""Draw every Fesium brand asset from one geometry definition.

Authoring-time only. The files it produces are committed, so nothing here runs
when Fesium runs:

    python -m pip install pillow
    python scripts/build_brand.py

Why a script rather than hand-authored files: the old assets drifted apart.
The mark was still neon ``#73F0FF`` from before the matte accent pass, the
social preview set its wordmark in Arial while the app ships its own face, and
the two disagreed about the mark's proportions. One definition below now feeds the SVG,
the banner, the social preview and the icons, so they cannot disagree again.

Two decisions are worth stating, because both were measured rather than
guessed:

**The mark carries its own ground.** The previous mark was transparent with
every stroke at ``stroke-opacity="0.28"``. In a README that means it sits on
whatever ground the reader's GitHub theme supplies - 2.12:1 against the dark
canvas and 1.10:1 against the light one, where the WCAG floor for a graphical
object is 3:1. The tile is opaque, and the banner and social preview bake a
dark ground in, so both render identically in either GitHub theme.

**The small sizes get their own artwork.** A ring inside the tile plus a
crossing orbit reads at 120px and turns to mush at 32. The shipped mark keeps
one orbit and a nucleus, and the 16px icon entry redraws them heavier rather
than downscaling artwork built for 512.
"""

import struct
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND_DIR = ROOT / "docs" / "assets" / "brand"
ICON_DIR = ROOT / "src" / "fesium" / "assets" / "icons"
FONT_DIR = ROOT / "src" / "fesium" / "assets" / "fonts"

# Straight from src/fesium/ui/theme/tokens.py. The brand and the app read from
# the same palette now; they did not before.
ACCENT = (93, 169, 179)        # accent.primary  #5DA9B3
GROUND = (18, 20, 25)          # bg.app          #121419
INK = (238, 243, 247)          # text.primary    #eef3f7
MUTED = (143, 154, 168)        # text.secondary  #8f9aa8
BORDER = (43, 52, 64)          # border.default  #2b3440

BOX = 512                      # the mark's design canvas
SUPERSAMPLE = 8                # Pillow has no anti-aliased stroking of its own

# The mark, in design units. Tuned at 32px, not at 512.
TILE_INSET = 28
ORBIT_RX, ORBIT_RY = 186, 84
ORBIT_TILT = 24                # counter-clockwise, matching the SVG's rotate(-24)
ORBIT_STROKE = 52
NUCLEUS_R = 52
# The 16px entry, redrawn heavier so the shapes survive at that size.
SMALL_ORBIT_STROKE = 76
SMALL_NUCLEUS_R = 74


def _blank(scale: int) -> Image.Image:
    return Image.new("RGBA", (BOX * scale, BOX * scale), (0, 0, 0, 0))


def _orbit_layer(scale: int, stroke: int) -> Image.Image:
    """The tilted orbit, on its own layer so it can rotate about the centre."""
    layer = _blank(scale)
    c = BOX / 2
    ImageDraw.Draw(layer).ellipse(
        [(c - ORBIT_RX) * scale, (c - ORBIT_RY) * scale,
         (c + ORBIT_RX) * scale, (c + ORBIT_RY) * scale],
        outline=GROUND + (255,), width=int(stroke * scale))
    return layer.rotate(ORBIT_TILT, resample=Image.BICUBIC,
                        center=(c * scale, c * scale))


def draw_mark(size: int, *, small: bool = False) -> Image.Image:
    """The mark at ``size`` px, drawn large and downscaled for the edges."""
    scale = SUPERSAMPLE
    stroke = SMALL_ORBIT_STROKE if small else ORBIT_STROKE
    nucleus = SMALL_NUCLEUS_R if small else NUCLEUS_R

    img = _blank(scale)
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [TILE_INSET * scale, TILE_INSET * scale,
         (BOX - TILE_INSET) * scale, (BOX - TILE_INSET) * scale],
        fill=ACCENT + (255,))
    img.alpha_composite(_orbit_layer(scale, stroke))
    c = BOX / 2
    ImageDraw.Draw(img).ellipse(
        [(c - nucleus) * scale, (c - nucleus) * scale,
         (c + nucleus) * scale, (c + nucleus) * scale], fill=GROUND + (255,))
    return img.resize((size, size), Image.LANCZOS)


def write_mark_svg(path: Path) -> None:
    """The same geometry as SVG, for anywhere a vector is wanted.

    The viewBox stays 0 0 512 512: tests/unit/test_brand_asset_layout.py
    asserts it, and every size below is derived from that canvas.
    """
    hexof = "#%02x%02x%02x"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" '
        'role="img" aria-label="Fesium">\n'
        f'  <rect x="{TILE_INSET}" y="{TILE_INSET}" '
        f'width="{BOX - 2 * TILE_INSET}" height="{BOX - 2 * TILE_INSET}" '
        f'fill="{hexof % ACCENT}" />\n'
        f'  <ellipse cx="256" cy="256" rx="{ORBIT_RX}" ry="{ORBIT_RY}" '
        f'fill="none" stroke="{hexof % GROUND}" stroke-width="{ORBIT_STROKE}" '
        f'transform="rotate(-{ORBIT_TILT} 256 256)" />\n'
        f'  <circle cx="256" cy="256" r="{NUCLEUS_R}" '
        f'fill="{hexof % GROUND}" />\n'
        "</svg>\n",
        encoding="utf-8")


REGULAR = "AtkinsonHyperlegible-Regular.ttf"
BOLD = "AtkinsonHyperlegible-Bold.ttf"


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a bundled face straight from the app's own font directory.

    The brand sets its wordmark in the face the app writes in, so the two
    cannot drift apart again the way Arial and Sora did.
    """
    return ImageFont.truetype(str(FONT_DIR / name), size)


def ink_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    """Width and height of the marks a string actually leaves.

    Pillow's anchors are relative to the font's ascender and baseline, not to
    the ink, so stacking by anchor leaves gaps that depend on which letters
    happen to have descenders. Both layouts below stack measured ink instead,
    which is why the wordmark and its tagline no longer collide.
    """
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def draw_ink(draw, x, y, text, font, fill, *, centre: bool = False) -> tuple[int, int]:
    """Draw ``text`` so its ink starts exactly at ``y`` (and at ``x``, or about it)."""
    left, top, right, bottom = font.getbbox(text)
    width, height = right - left, bottom - top
    origin_x = x - width / 2 if centre else x
    draw.text((origin_x - left, y - top), text, font=font, fill=fill)
    return width, height


def build_banner(path: Path, height: int = 300) -> None:
    """The README banner: mark, wordmark and one line of what it is.

    It bakes the dark ground rather than shipping a transparent logo, so the
    header reads the same for a visitor on GitHub's light theme as on its dark
    one. That is the whole reason this file exists as a PNG rather than the
    transparent SVG the README used to inline.

    The canvas is sized to the lockup rather than fixed, because a fixed width
    left the composition stranded against a third of a canvas of dead space.
    """
    margin, gap, mark_size, line_gap = 76, 40, 152, 14
    wordmark = load_font(BOLD, 78)
    tagline = load_font(REGULAR, 26)
    words, tag = "Fesium", "Local dev tools for students and developers"

    word_w, word_h = ink_size(wordmark, words)
    tag_w, tag_h = ink_size(tagline, tag)
    text_w = max(word_w, tag_w)
    text_h = word_h + line_gap + tag_h
    width = margin + mark_size + gap + text_w + margin

    img = Image.new("RGB", (width, height), GROUND)
    draw = ImageDraw.Draw(img)
    # One accent rule along the bottom, thick enough to survive GitHub scaling
    # the image down to the width of a README column.
    draw.rectangle([0, height - 6, width, height], fill=ACCENT)

    mark = draw_mark(mark_size)
    img.paste(mark, (margin, (height - 6 - mark_size) // 2), mark)

    text_x = margin + mark_size + gap
    text_y = (height - 6 - text_h) // 2
    draw_ink(draw, text_x, text_y, words, wordmark, INK)
    draw_ink(draw, text_x, text_y + word_h + line_gap, tag, tagline, MUTED)

    img.save(path, optimize=True)


def build_social_preview(path: Path, width: int = 1280, height: int = 640) -> None:
    """GitHub's social preview, at the size GitHub asks for.

    The previous version tiled a 160px faceted pattern across the canvas, which
    resolved into visible horizontal banding, and set the wordmark in Arial.
    This one keeps the ground plain and the wordmark in the app's own face.
    """
    mark_size, mark_gap, line_gap = 216, 58, 20
    wordmark = load_font(BOLD, 92)
    tagline = load_font(REGULAR, 30)
    words, tag = "Fesium", "Local dev tools for students and developers"

    word_w, word_h = ink_size(wordmark, words)
    tag_w, tag_h = ink_size(tagline, tag)
    stack = mark_size + mark_gap + word_h + line_gap + tag_h
    # Sits a little above centre: a block of text reads as low when it is
    # measured to the exact middle.
    top = (height - stack) // 2 - 16

    img = Image.new("RGB", (width, height), GROUND)
    draw = ImageDraw.Draw(img)

    # A soft accent wash behind the mark, drawn as concentric rings rather than
    # a bitmap gradient so it stays banding-free at this size.
    cx, cy = width // 2, top + mark_size // 2
    for radius in range(320, 0, -2):
        weight = (1 - radius / 320) * 0.13
        blend = tuple(round(GROUND[i] + (ACCENT[i] - GROUND[i]) * weight)
                      for i in range(3))
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=blend)

    mark = draw_mark(mark_size)
    img.paste(mark, (cx - mark_size // 2, top), mark)

    text_y = top + mark_size + mark_gap
    draw_ink(draw, cx, text_y, words, wordmark, INK, centre=True)
    draw_ink(draw, cx, text_y + word_h + line_gap, tag, tagline, MUTED, centre=True)

    img.save(path, optimize=True)


def write_ico(path: Path, entries: list[tuple[int, Image.Image]]) -> None:
    """Write a multi-size ICO with per-size artwork.

    Pillow's own ICO writer resizes one source image for every entry, which
    would throw away the redrawn 16px mark. The container is simple enough to
    write directly, and Windows has accepted PNG-compressed entries since Vista.
    """
    blobs = []
    for _, image in entries:
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        blobs.append(buffer.getvalue())

    offset = 6 + 16 * len(entries)
    header = struct.pack("<HHH", 0, 1, len(entries))
    directory = b""
    for (size, _), blob in zip(entries, blobs, strict=True):
        directory += struct.pack(
            "<BBBBHHII", size if size < 256 else 0, size if size < 256 else 0,
            0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path.write_bytes(header + directory + b"".join(blobs))


def main() -> int:
    if not FONT_DIR.exists():
        print(f"bundled fonts not found at {FONT_DIR}", file=sys.stderr)
        return 1
    BRAND_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    write_mark_svg(BRAND_DIR / "fesium-orbit.svg")
    build_banner(BRAND_DIR / "fesium-banner.png")
    build_social_preview(BRAND_DIR / "fesium-social-preview.png")

    master = draw_mark(256)
    master.save(ICON_DIR / "fesium-orbit-256.png", optimize=True)
    write_ico(ICON_DIR / "fesium-orbit.ico", [
        (16, draw_mark(16, small=True)),
        (32, draw_mark(32)),
        (48, draw_mark(48)),
        (64, draw_mark(64)),
        (128, draw_mark(128)),
        (256, master),
    ])

    for produced in (
        BRAND_DIR / "fesium-orbit.svg",
        BRAND_DIR / "fesium-banner.png",
        BRAND_DIR / "fesium-social-preview.png",
        ICON_DIR / "fesium-orbit-256.png",
        ICON_DIR / "fesium-orbit.ico",
    ):
        print(f"{produced.relative_to(ROOT)!s:<52} {produced.stat().st_size:>7d} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
