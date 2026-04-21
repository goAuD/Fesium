from types import SimpleNamespace

from fesium.ui.theme import font_loader


def test_register_bundled_fonts_loads_each_unique_font_once_on_windows(monkeypatch):
    calls = []

    monkeypatch.setattr(font_loader.sys, "platform", "win32")
    monkeypatch.setattr(font_loader, "_LOADED_FONTS", set())
    monkeypatch.setattr(
        font_loader,
        "ctypes",
        SimpleNamespace(
            windll=SimpleNamespace(
                gdi32=SimpleNamespace(
                    AddFontResourceExW=lambda path, flags, reserved: calls.append((path, flags)) or 1
                )
            )
        ),
    )

    font_loader.register_bundled_fonts()

    assert len(calls) == 3
    assert all(flags == font_loader.FR_PRIVATE for _, flags in calls)
