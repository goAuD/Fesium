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
    assert __version__ == "2.0.0"


def test_release_version_targets_v2():
    assert __version__ == "2.0.0"


def test_package_version_comes_from_the_single_source_module():
    assert __version__ == source_version


def test_pyproject_reads_the_version_from_the_package():
    """Two hardcoded version strings drift. Keep exactly one."""
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'dynamic = ["version"]' in pyproject
    assert 'version = {attr = "fesium._version.__version__"}' in pyproject
