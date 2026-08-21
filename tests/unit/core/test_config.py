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


def test_config_defaults_to_restoring_the_last_project(tmp_path):
    config = Config(config_dir=tmp_path / ".fesium")

    assert config.restore_last_project is True
    assert config.default_project == ""


def test_config_persists_the_startup_preferences(tmp_path):
    config = Config(config_dir=tmp_path / ".fesium")
    config.default_project = str(tmp_path)
    config.restore_last_project = False

    reloaded = Config(config_dir=tmp_path / ".fesium")
    assert reloaded.default_project == str(tmp_path)
    assert reloaded.restore_last_project is False


def test_config_backfills_new_keys_into_an_older_config_file(tmp_path):
    """Existing installs have a config.json written before these keys existed."""
    config_dir = tmp_path / ".fesium"
    config_dir.mkdir()
    (config_dir / "config.json").write_text('{"port": 8123}', encoding="utf-8")

    config = Config(config_dir=config_dir)

    assert config.port == 8123
    assert config.restore_last_project is True
    assert config.default_project == ""
