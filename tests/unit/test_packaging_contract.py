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
    assert '"fesium.assets" = ["icons/*.png", "icons/*.ico"]' in PYPROJECT
    assert '"fesium.assets.fonts" = ["*.ttf", "*.md", "licenses/*.txt"]' in PYPROJECT


def test_font_licences_sit_next_to_the_fonts_they_cover():
    """The OFL requires the licence to travel with the redistributed font."""
    licences = Path("src/fesium/assets/fonts/licenses")

    assert sorted(path.name for path in licences.glob("*.txt")) == [
        "IBMPlexSans-OFL.txt",
        "JetBrainsMono-OFL.txt",
        "Sora-OFL.txt",
    ]
