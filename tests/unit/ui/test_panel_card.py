from fesium.ui.widgets.panel_card import resolve_panel_surface


def test_resolve_panel_surface_supports_default_variant():
    surface = resolve_panel_surface("default")
    assert surface["fg_color"] == "bg.panel"
    assert surface["border_color"] == "border.default"


def test_resolve_panel_surface_supports_inset_variants():
    inset = resolve_panel_surface("inset")
    strong = resolve_panel_surface("inset_strong")

    assert inset["fg_color"] == "bg.panel_alt"
    assert strong["fg_color"] == "bg.app"
    assert strong["border_color"] == "border.soft"


def test_resolve_panel_surface_rejects_unknown_variant():
    try:
        resolve_panel_surface("unknown")
    except ValueError as exc:
        assert "Unknown panel surface variant" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown panel surface variant")
