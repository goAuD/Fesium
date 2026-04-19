from fesium.ui.widgets.panel_card import resolve_panel_inset_geometry, resolve_panel_surface


def test_resolve_panel_surface_supports_default_variant():
    surface = resolve_panel_surface("default")
    assert surface["outer_fg"] == "bg.panel"
    assert surface["inner_fg"] is None


def test_resolve_panel_surface_supports_inset_variants():
    inset = resolve_panel_surface("inset")
    strong = resolve_panel_surface("inset_strong")

    assert inset["inner_fg"] == "bg.panel_alt"
    assert strong["inner_fg"] == "bg.app"


def test_resolve_panel_surface_rejects_unknown_variant():
    try:
        resolve_panel_surface("unknown")
    except ValueError as exc:
        assert "Unknown panel surface variant" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown panel surface variant")


def test_resolve_panel_inset_geometry_keeps_inner_radius_smaller_than_outer():
    geometry = resolve_panel_inset_geometry("inset")

    assert geometry["padding"] >= 3
    assert geometry["inner_corner_radius"] < geometry["outer_corner_radius"]


def test_resolve_panel_inset_geometry_supports_strong_variant():
    geometry = resolve_panel_inset_geometry("inset_strong")

    assert geometry["padding"] >= 3
