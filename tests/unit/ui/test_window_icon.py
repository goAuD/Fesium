from pathlib import Path

from fesium.ui.theme.window_icon import apply_window_icon, get_window_icon_paths


def test_get_window_icon_paths_point_to_expected_runtime_assets():
    paths = get_window_icon_paths()
    assert paths["png"].name == "fesium-orbit-256.png"
    assert paths["ico"].name == "fesium-orbit.ico"


def test_runtime_icon_files_exist():
    paths = get_window_icon_paths()
    assert Path(paths["png"]).exists()
    assert Path(paths["ico"]).exists()


def test_apply_window_icon_uses_png_asset(monkeypatch):
    fake_image = object()

    class FakeWindow:
        def __init__(self):
            self.iconphoto_args = None
            self.iconbitmap_args = None

        def iconphoto(self, *args):
            self.iconphoto_args = args

        def iconbitmap(self, **kwargs):
            self.iconbitmap_args = kwargs

    monkeypatch.setattr("fesium.ui.theme.window_icon.tk.PhotoImage", lambda file: fake_image)
    monkeypatch.setattr("fesium.ui.theme.window_icon.sys.platform", "linux")

    window = FakeWindow()
    assert apply_window_icon(window) is True
    assert window.iconphoto_args == (True, fake_image)
    assert window.iconbitmap_args is None
    assert window._fesium_icon_image is fake_image
