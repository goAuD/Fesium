from pathlib import Path


def test_brand_asset_directories_exist():
    assert Path("docs/assets/brand").is_dir()
    assert Path("docs/assets/screenshots").is_dir()


def test_legacy_root_images_are_removed():
    assert not Path("nanoserver.png").exists()
    assert not Path("social_preview.png").exists()
