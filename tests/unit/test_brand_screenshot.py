import struct
from pathlib import Path


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        assert signature == b"\x89PNG\r\n\x1a\n"
        length = struct.unpack(">I", handle.read(4))[0]
        assert length == 13
        chunk = handle.read(4)
        assert chunk == b"IHDR"
        width = struct.unpack(">I", handle.read(4))[0]
        height = struct.unpack(">I", handle.read(4))[0]
        return width, height


def test_overview_screenshot_exists_and_is_large_enough():
    screenshot = Path("docs/assets/screenshots/fesium-overview.png")
    assert screenshot.exists()
    width, height = read_png_dimensions(screenshot)
    assert width >= 1000
    assert height >= 600


def test_readme_mentions_the_new_overview_screenshot():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docs/assets/screenshots/fesium-overview.png" in readme
