from pathlib import Path

from fesium.assets.fonts.font_manifest import FONT_FILES
from fesium.ui.theme.styles import resolve_button_style
from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS


def test_graphite_grid_color_tokens_include_required_keys():
    required = {
        "bg.app",
        "bg.sidebar",
        "bg.panel",
        "text.primary",
        "accent.primary",
        "accent.success",
        "accent.warning",
        "accent.danger",
    }
    assert required.issubset(COLOR_TOKENS.keys())


def test_font_manifest_points_to_local_files():
    assert FONT_FILES["heading"].name == "Sora[wght].ttf"
    assert FONT_FILES["body"].name == "IBMPlexSans[wdth,wght].ttf"
    assert FONT_FILES["body_medium"].name == "IBMPlexSans[wdth,wght].ttf"
    assert FONT_FILES["mono"].name == "JetBrainsMono-Regular.ttf"
    assert FONT_FILES["heading"].exists()
    assert FONT_FILES["body"].exists()
    assert FONT_FILES["mono"].exists()


def test_font_tokens_include_expected_roles():
    assert set(FONT_TOKENS.keys()) == {"heading", "section_heading", "body", "body_medium", "mono"}


def test_font_tokens_match_shell_density_scale():
    assert FONT_TOKENS["heading"] == ("Sora", 28, "bold")
    assert FONT_TOKENS["section_heading"] == ("Sora", 18, "bold")
    assert FONT_TOKENS["body"] == ("IBM Plex Sans", 16)
    assert FONT_TOKENS["body_medium"] == ("IBM Plex Sans", 16, "bold")
    assert FONT_TOKENS["mono"] == ("JetBrains Mono", 14)


def test_font_license_docs_exist():
    assert Path("src/fesium/assets/fonts/LICENSES.md").exists()
    assert Path("src/fesium/assets/fonts/licenses/Sora-OFL.txt").exists()
    assert Path("src/fesium/assets/fonts/licenses/IBMPlexSans-OFL.txt").exists()
    assert Path("src/fesium/assets/fonts/licenses/JetBrainsMono-OFL.txt").exists()


def test_resolve_button_style_primary_is_filled_accent():
    primary = resolve_button_style("primary")

    assert primary["fg_color"] == "accent.primary"
    assert primary["text_color"] == "bg.app"
    assert primary["border_color"] == "accent.primary"
    assert primary["border_width"] == 1


def test_resolve_button_style_secondary_is_ghost_with_accent_border():
    secondary = resolve_button_style("secondary")

    assert secondary["fg_color"] == "bg.panel"
    assert secondary["text_color"] == "accent.primary"
    assert secondary["border_color"] == "accent.primary"
    assert secondary["border_width"] == 1


def test_resolve_button_style_secondary_is_visually_distinct_from_primary():
    primary = resolve_button_style("primary")
    secondary = resolve_button_style("secondary")

    assert primary["fg_color"] != secondary["fg_color"]
    assert primary["text_color"] != secondary["text_color"]


def test_resolve_button_style_danger_uses_danger_accent():
    danger = resolve_button_style("danger")
    danger_secondary = resolve_button_style("danger_secondary")

    assert danger["fg_color"] == "accent.danger"
    assert danger["border_color"] == "accent.danger"
    assert danger_secondary["fg_color"] == "bg.panel"
    assert danger_secondary["text_color"] == "accent.danger"
    assert danger_secondary["border_color"] == "accent.danger"


def test_resolve_button_style_nav_active_uses_accent_border():
    nav_active = resolve_button_style("nav", active=True)

    assert nav_active["border_color"] == "accent.primary"
