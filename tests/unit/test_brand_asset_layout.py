import struct
import xml.etree.ElementTree as ET
from pathlib import Path


def test_brand_asset_directories_exist():
    assert Path("docs/assets/brand").is_dir()
    assert Path("docs/assets/screenshots").is_dir()


def test_legacy_root_images_are_removed():
    assert not Path("nanoserver.png").exists()
    assert not Path("social_preview.png").exists()


def test_master_icon_svg_exists_and_has_expected_viewbox():
    svg_path = Path("docs/assets/brand/fesium-orbit.svg")
    assert svg_path.exists()

    root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 512 512"


def test_social_preview_prompt_mentions_required_terms():
    prompt = Path("docs/assets/brand/fesium-social-preview-prompt.md").read_text(encoding="utf-8").lower()
    for token in [
        "fesium",
        "pure orbit",
        "1280x640",
        "faceted",
        "graphite",
        "nano banana 2",
    ]:
        assert token in prompt


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


def test_social_preview_png_matches_github_recommendation():
    png_path = Path("docs/assets/brand/fesium-social-preview.png")
    assert png_path.exists()
    assert png_path.stat().st_size < 1_000_000
    assert read_png_dimensions(png_path) == (1280, 640)


def test_social_preview_source_svg_exists():
    assert Path("docs/assets/brand/fesium-social-preview.svg").exists()


def test_readme_uses_new_brand_assets_and_repo_slug():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docs/assets/brand/fesium-orbit.svg" in readme
    assert "https://github.com/goAuD/Fesium.git" in readme
    assert "cd Fesium" in readme
    assert "nanoserver.png" not in readme
    assert "social_preview.png" not in readme
    assert "NanoServer/" not in readme


def test_roadmap_uses_fesium_name():
    roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
    assert roadmap.startswith("# Fesium Roadmap")
    assert "NanoServer" not in roadmap


def test_legacy_design_system_doc_is_removed():
    assert not Path("DESIGN_SYSTEM.md").exists()
