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
