from fesium.ui.shell import DEFAULT_WINDOW_GEOMETRY, MIN_WINDOW_SIZE


def test_shell_uses_desktop_density_default_geometry():
    assert DEFAULT_WINDOW_GEOMETRY == "1400x960"


def test_shell_uses_desktop_density_minimum_size():
    assert MIN_WINDOW_SIZE == (1100, 760)
