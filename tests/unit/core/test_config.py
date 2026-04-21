from fesium.core.config import Config
from fesium.core.paths import AppPaths


def test_app_paths_defaults_to_fesium_directory(tmp_path):
    paths = AppPaths(home_dir=tmp_path)
    assert paths.config_dir == tmp_path / ".fesium"


def test_config_roundtrip_uses_json_file(tmp_path):
    config = Config(config_dir=tmp_path / ".fesium")
    config.set("port", 9001)

    loaded = Config(config_dir=tmp_path / ".fesium")
    assert loaded.port == 9001


def test_config_prefers_legacy_directory_when_migrating(tmp_path):
    legacy_dir = tmp_path / ".nanoserver"
    legacy_dir.mkdir()
    (legacy_dir / "config.json").write_text('{"port": 8123}', encoding="utf-8")

    paths = AppPaths(home_dir=tmp_path)
    assert paths.legacy_config_dir == legacy_dir

    config = Config(
        config_dir=paths.config_dir,
        legacy_config_dir=paths.legacy_config_dir,
    )
    assert config.port == 8123


def test_config_uses_updated_shell_geometry_by_default(tmp_path):
    config = Config(config_dir=tmp_path / ".fesium")

    assert config.get("window_geometry") == "1400x960"
