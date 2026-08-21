from pathlib import Path

PYPROJECT = Path("pyproject.toml").read_text(encoding="utf-8")


def test_console_script_is_declared():
    assert '[project.scripts]' in PYPROJECT
    assert 'fesium = "fesium.app:main"' in PYPROJECT


def test_bundled_assets_are_declared_as_package_data():
    """Fesium is offline-first, so an install that drops the bundled fonts and
    icons is a broken install. setuptools ships no non-Python file unless it is
    declared, and nothing else in the suite would notice them going missing.
    """
    for pattern in ("icons/*.png", "icons/*.ico", "icons/lucide/*.png", "icons/lucide/*.svg"):
        assert f'"{pattern}"' in PYPROJECT, pattern
    assert '"fesium.assets.fonts" = ["*.ttf", "*.md", "licenses/*.txt"]' in PYPROJECT


def test_pillow_is_declared():
    """customtkinter imports PIL for CTkImage without declaring it, and Fesium
    tints its icons through Pillow, so the dependency is ours to state."""
    assert "pillow" in PYPROJECT.lower()
    assert "pillow" in Path("requirements.txt").read_text(encoding="utf-8").lower()


def test_icon_licence_ships_with_the_icons():
    """ISC requires the copyright and permission notice to travel with copies."""
    licence = Path("src/fesium/assets/icons/lucide/LICENSE.txt")

    assert licence.exists()
    text = licence.read_text(encoding="utf-8")
    assert "ISC License" in text
    assert "Permission to use, copy, modify" in text
    assert '"icons/lucide/*.txt"' in PYPROJECT


def test_font_licences_sit_next_to_the_fonts_they_cover():
    """The OFL requires the licence to travel with the redistributed font."""
    licences = Path("src/fesium/assets/fonts/licenses")

    assert sorted(path.name for path in licences.glob("*.txt")) == [
        "IBMPlexSans-OFL.txt",
        "JetBrainsMono-OFL.txt",
        "Sora-OFL.txt",
    ]
