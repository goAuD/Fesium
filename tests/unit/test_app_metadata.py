from pathlib import Path

from fesium import __version__
from fesium._version import __version__ as source_version
from fesium.app import AppMetadata, build_window_title


def test_build_window_title_includes_brand_and_version():
    assert build_window_title("1.0.0") == "Fesium v1.0.0"


def test_app_metadata_defaults_to_fesium_brand():
    metadata = AppMetadata(
        name="Fesium",
        tagline="Local dev tools for students and developers",
    )
    assert metadata.name == "Fesium"
    assert "students and developers" in metadata.tagline
    assert AppMetadata.__dataclass_params__.frozen is True


def test_release_version_is_the_one_we_mean_to_ship():
    """Pinned rather than pattern-matched, so a bump is always deliberate."""
    assert __version__ == "2.2.0"


def test_changelog_carries_a_section_for_the_shipped_version():
    """The repo has drifted before by shipping work the changelog denied.

    A version with no section means either the bump or the notes were
    forgotten, and which one is not knowable afterwards.
    """
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert f"## [{__version__}] - " in changelog


def test_release_notes_exist_for_the_shipped_version():
    assert Path(f"docs/release/v{__version__}.md").exists()


def test_package_version_comes_from_the_single_source_module():
    assert __version__ == source_version


def test_pyproject_reads_the_version_from_the_package():
    """Two hardcoded version strings drift. Keep exactly one."""
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'dynamic = ["version"]' in pyproject
    assert 'version = {attr = "fesium._version.__version__"}' in pyproject
