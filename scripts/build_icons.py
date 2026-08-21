"""Rasterise the bundled Lucide SVG sources into PNGs.

Authoring-time only. The PNGs it produces are committed, so nothing here runs
when Fesium runs and neither dependency below is needed to use the app:

    python -m pip install svgelements pillow
    python scripts/build_icons.py

Lucide icons are stroke geometry on a 24x24 grid: width 2, round caps, round
joins, no fill. That is what this reproduces. Paths are flattened to polylines
by svgelements (which handles the arcs and beziers), drawn at 8x and scaled
down, which is where the anti-aliasing comes from - Pillow has no native
stroking with round caps, so caps and joins are painted as discs.

Output is white on transparent. Colour is applied at runtime by
`fesium.ui.widgets.icon`, so one file serves every state an icon appears in.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw
from svgelements import SVG, Close, CubicBezier, Line, Move, QuadraticBezier, Shape
from svgelements import Path as SvgPath

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "src" / "fesium" / "assets" / "icons" / "lucide"

VIEWBOX = 24
STROKE = 2
SUPERSAMPLE = 8
# 1x for the sidebar, 2x so CTkImage stays sharp on a HiDPI display.
SIZES = {"": 20, "@2x": 40}
# Curve flattening. 24 steps per segment is well under a pixel of error at 8x.
STEPS = 24


def flatten(path: SvgPath) -> list[list[tuple[float, float]]]:
    """Split a path into subpaths of points, so a Move never draws a line."""
    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []

    for segment in path.segments():
        if isinstance(segment, Move):
            if len(current) > 1:
                subpaths.append(current)
            current = [(segment.end.x, segment.end.y)]
        elif isinstance(segment, Line | Close):
            current.append((segment.end.x, segment.end.y))
        elif isinstance(segment, CubicBezier | QuadraticBezier):
            current.extend((segment.point(i / STEPS).x, segment.point(i / STEPS).y) for i in range(1, STEPS + 1))
        else:  # Arc, and anything else svgelements can sample
            current.extend((segment.point(i / STEPS).x, segment.point(i / STEPS).y) for i in range(1, STEPS + 1))

    if len(current) > 1:
        subpaths.append(current)
    return subpaths


def render(svg_path: Path, size: int) -> Image.Image:
    canvas_size = size * SUPERSAMPLE
    scale = canvas_size / VIEWBOX
    stroke = STROKE * scale
    radius = stroke / 2

    image = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    document = SVG.parse(str(svg_path))
    for element in document.elements():
        if not isinstance(element, Shape):
            continue
        for points in flatten(SvgPath(element)):
            scaled = [(x * scale, y * scale) for x, y in points]
            draw.line(scaled, fill=(255, 255, 255, 255), width=round(stroke), joint="curve")
            # Round caps and joins: Pillow's "curve" joint still leaves square
            # ends, and a disc at every vertex covers both cases.
            for x, y in scaled:
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, 255))

    return image.resize((size, size), Image.LANCZOS)


def main() -> int:
    sources = sorted(ICON_DIR.glob("*.svg"))
    if not sources:
        print(f"no SVG sources in {ICON_DIR}", file=sys.stderr)
        return 1

    for source in sources:
        for suffix, size in SIZES.items():
            target = ICON_DIR / f"{source.stem}{suffix}.png"
            render(source, size).save(target)
            print(f"  {target.relative_to(ROOT).as_posix()}  {size}x{size}")

    print(f"\n{len(sources)} icons, {len(sources) * len(SIZES)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
