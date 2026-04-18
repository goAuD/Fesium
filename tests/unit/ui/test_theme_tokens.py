from pathlib import Path

from fesium.assets.fonts.font_manifest import FONT_FILES
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
    assert set(FONT_TOKENS.keys()) == {"heading", "body", "body_medium", "mono"}


def test_font_license_docs_exist():
    assert Path("src/fesium/assets/fonts/LICENSES.md").exists()
    assert Path("src/fesium/assets/fonts/licenses/Sora-OFL.txt").exists()
    assert Path("src/fesium/assets/fonts/licenses/IBMPlexSans-OFL.txt").exists()
    assert Path("src/fesium/assets/fonts/licenses/JetBrainsMono-OFL.txt").exists()
