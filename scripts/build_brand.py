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

Decisions worth stating, because each was measured rather than guessed:

**The mark is line art, and its colour follows its ground.** An orbit, a
nucleus and one electron riding the ring - three shapes, one colour, no
fill block. Monochrome line work reads as engineering rather than decoration,
and a single colour survives every size from favicon to banner. The colour is
the accent on dark grounds (7.8:1 against ``#121419``) and a deepened shade of
the same hue on light ones (4.6:1 against white), because the raw accent
measures 2.7:1 there - under the 3:1 floor for a graphical object. Same
geometry everywhere; only the ink changes with the paper.

**The social preview carries a light ground.** The previous preview baked the
app's dark background in and measured a mean luminance of 29/255 - on
GitHub's card it read as a black rectangle, which is what it mostly was. This
one inverts: near-white ground, deep-teal mark, dark wordmark. It reads
instantly in both GitHub themes, where a dark card disappears into the dark
one and blends into the light one.

**The small sizes get their own artwork.** The full mark reads at 120px and
turns to mush at 32. The shipped icon keeps the tile, and the 16px entry
redraws every shape heavier rather than downscaling artwork built for 512.
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

# The accent deepened just enough to clear 3:1 against white (it measures
# 4.6:1). Same hue as ACCENT, so the two read as one brand on either ground.
ACCENT_DEEP = (61, 126, 136)   # #3d7e88
# MUTED deepened for text on the light ground, for the same reason.
MUTED_DEEP = (90, 102, 115)    # #5a6673

BOX = 512                      # the mark's design canvas
SUPERSAMPLE = 8                # Pillow has no anti-aliased stroking of its own

# The mark, in design units. Tuned at 32px, not at 512.
TILE_INSET = 28
ORBIT_RX, ORBIT_RY = 196, 86
ORBIT_TILT = 24                # counter-clockwise, matching the SVG's rotate(-24)
ORBIT_STROKE = 36
NUCLEUS_R = 54
ELECTRON_R = 24
# The 16px entry, redrawn heavier so the shapes survive at that size.
SMALL_ORBIT_STROKE = 58
SMALL_NUCLEUS_R = 74
SMALL_ELECTRON_R = 36


def _electron_center() -> tuple[float, float]:
    """Where the electron sits: on the ring, at its rotated left extreme.

    The unrotated ellipse's leftmost point is ``(cx - RX, cy)``; the orbit
    layer is then rotated counter-clockwise by ORBIT_TILT about the centre,
    and the electron has to land on the stroke, not near it.
    """
    import math

    c = BOX / 2
    dx, dy = -ORBIT_RX, 0.0
    theta = math.radians(ORBIT_TILT)
    # Counter-clockwise in screen coordinates (y grows downward).
    return c + dx * math.cos(theta) + dy * math.sin(theta), \
        c - dx * math.sin(theta) + dy * math.cos(theta)


def _blank(scale: int) -> Image.Image:
    return Image.new("RGBA", (BOX * scale, BOX * scale), (0, 0, 0, 0))


def _orbit_layer(scale: int, stroke: int) -> Image.Image:
    """The tilted orbit, on its own layer so it can rotate about the centre."""
    layer = _blank(scale)
    c = BOX / 2
    ImageDraw.Draw(layer).ellipse(
        [(c - ORBIT_RX) * scale, (c - ORBIT_RY) * scale,
         (c + ORBIT_RX) * scale, (c + ORBIT_RY) * scale],
        outline=(0, 0, 0, 255), width=int(stroke * scale))
    return layer.rotate(ORBIT_TILT, resample=Image.BICUBIC,
                        center=(c * scale, c * scale))


def draw_line_mark(size: int, color: tuple[int, int, int], *,
                   small: bool = False) -> Image.Image:
    """The mark as monochrome line art on transparency, at ``size`` px.

    Orbit, nucleus and electron all take ``color`` - one ink, three shapes.
    Drawn large and downscaled so the edges stay clean.
    """
    scale = SUPERSAMPLE
    stroke = SMALL_ORBIT_STROKE if small else ORBIT_STROKE
    nucleus = SMALL_NUCLEUS_R if small else NUCLEUS_R
    electron = SMALL_ELECTRON_R if small else ELECTRON_R

    img = _blank(scale)
    # The orbit layer is drawn in opaque black and recoloured, because the
    # rotation resamples alpha and would fade a coloured stroke's edges.
    orbit = _orbit_layer(scale, stroke)
    solid = Image.new("RGBA", orbit.size, color + (255,))
    img.paste(solid, (0, 0), orbit)

    draw = ImageDraw.Draw(img)
    c = BOX / 2
    draw.ellipse(
        [(c - nucleus) * scale, (c - nucleus) * scale,
         (c + nucleus) * scale, (c + nucleus) * scale], fill=color + (255,))
    ex, ey = _electron_center()
    draw.ellipse(
        [(ex - electron) * scale, (ey - electron) * scale,
         (ex + electron) * scale, (ey + electron) * scale], fill=color + (255,))
    return img.resize((size, size), Image.LANCZOS)


def draw_mark(size: int, *, small: bool = False) -> Image.Image:
    """The tile mark for the app icon: accent square, ground-coloured line art.

    The tile exists because an icon floats among other icons on surfaces this
    project does not control - a taskbar, a desktop - and carries its own
    ground the way the banner does.
    """
    scale = SUPERSAMPLE
    img = _blank(scale)
    ImageDraw.Draw(img).rectangle(
        [TILE_INSET * scale, TILE_INSET * scale,
         (BOX - TILE_INSET) * scale, (BOX - TILE_INSET) * scale],
        fill=ACCENT + (255,))
    line = draw_line_mark(BOX, GROUND, small=small)
    img.alpha_composite(line.resize((BOX * scale, BOX * scale), Image.LANCZOS))
    return img.resize((size, size), Image.LANCZOS)


def write_mark_svg(path: Path, color: tuple[int, int, int]) -> None:
    """The line mark as SVG, for anywhere a vector is wanted.

    Transparent by design: the caller picks the variant whose ink suits its
    ground (ACCENT on dark, ACCENT_DEEP on light). The viewBox stays
    0 0 512 512: tests/unit/test_brand_asset_layout.py asserts it, and every
    size below is derived from that canvas.
    """
    hexof = "#%02x%02x%02x"
    ex, ey = _electron_center()
    # newline="\n" keeps the bytes identical on every platform: this file is
    # read back as raw bytes by build_site.py's data_uri, so a Windows CRLF
    # here would bake itself into the site's embedded copy and fail the
    # site-contract test on every other OS.
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" '
        'role="img" aria-label="Fesium">\n'
        f'  <ellipse cx="256" cy="256" rx="{ORBIT_RX}" ry="{ORBIT_RY}" '
        f'fill="none" stroke="{hexof % color}" stroke-width="{ORBIT_STROKE}" '
        f'transform="rotate(-{ORBIT_TILT} 256 256)" />\n'
        f'  <circle cx="256" cy="256" r="{NUCLEUS_R}" '
        f'fill="{hexof % color}" />\n'
        f'  <circle cx="{ex:.0f}" cy="{ey:.0f}" r="{ELECTRON_R}" '
        f'fill="{hexof % color}" />\n'
        "</svg>\n",
        encoding="utf-8", newline="\n")


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
    one. The mark sits as line art in the accent - quieter than a filled tile
    and consistent with the SVG the repo ships beside it.

    The canvas is sized to the lockup rather than fixed, because a fixed width
    left the composition stranded against a third of a canvas of dead space.
    """
    margin, gap, mark_size, line_gap = 76, 44, 148, 14
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

    mark = draw_line_mark(mark_size, ACCENT)
    img.paste(mark, (margin, (height - 6 - mark_size) // 2), mark)

    text_x = margin + mark_size + gap
    text_y = (height - 6 - text_h) // 2
    draw_ink(draw, text_x, text_y, words, wordmark, INK)
    draw_ink(draw, text_x, text_y + word_h + line_gap, tag, tagline, MUTED)

    img.save(path, optimize=True)


def build_social_preview(path: Path, width: int = 1280, height: int = 640) -> None:
    """GitHub's social preview, at the size GitHub asks for.

    The ground is light on purpose. The previous preview baked the app's dark
    background in and measured a mean luminance of 29/255, so GitHub's card
    rendered it as a black rectangle - the complaint that prompted this
    rework. Near-white ground, deep-teal mark, dark wordmark: it reads in both
    GitHub themes, where a dark card vanishes into the dark one.
    """
    mark_size, mark_gap, line_gap = 224, 56, 20
    wordmark = load_font(BOLD, 96)
    tagline = load_font(REGULAR, 30)
    words, tag = "Fesium", "Local dev tools for students and developers"

    word_w, word_h = ink_size(wordmark, words)
    tag_w, tag_h = ink_size(tagline, tag)
    stack = mark_size + mark_gap + word_h + line_gap + tag_h
    # Sits a little above centre: a block of text reads as low when it is
    # measured to the exact middle.
    top = (height - stack) // 2 - 16

    img = Image.new("RGB", (width, height), INK)
    draw = ImageDraw.Draw(img)
    # One accent rule along the bottom, tying the card to the banner.
    draw.rectangle([0, height - 10, width, height], fill=ACCENT)

    # A faint deep-teal wash behind the mark, drawn as concentric rings rather
    # than a bitmap gradient so it stays banding-free at this size.
    cx, cy = width // 2, top + mark_size // 2
    for radius in range(300, 0, -2):
        weight = (1 - radius / 300) * 0.07
        blend = tuple(round(INK[i] + (ACCENT_DEEP[i] - INK[i]) * weight)
                      for i in range(3))
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=blend)

    mark = draw_line_mark(mark_size, ACCENT_DEEP)
    img.paste(mark, (cx - mark_size // 2, top), mark)

    text_y = top + mark_size + mark_gap
    draw_ink(draw, cx, text_y, words, wordmark, GROUND, centre=True)
    draw_ink(draw, cx, text_y + word_h + line_gap, tag, tagline, MUTED_DEEP, centre=True)

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

    # The vector ships in the dark-ground ink; on a light surface use
    # ACCENT_DEEP, which the script emits nowhere by default but accepts here.
    write_mark_svg(BRAND_DIR / "fesium-orbit.svg", ACCENT)
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
