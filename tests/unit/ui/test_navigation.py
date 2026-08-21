from fesium.ui.navigation import build_navigation_items


def test_navigation_matches_design_spec():
    items = build_navigation_items()
    assert [item.id for item in items] == [
        "overview",
        "server",
        "database",
        "environment",
        "guide",
        "settings",
    ]
    assert items[3].label == "Diagnostics"
    assert items[4].label == "Guide"


def test_every_navigation_item_names_a_bundled_icon():
    """A missing PNG would only surface when the sidebar is built, which the
    headless suite never does."""
    from fesium.ui.widgets.icon import ICON_DIR

    for item in build_navigation_items():
        assert (ICON_DIR / f"{item.icon}.png").exists(), item.icon
        assert (ICON_DIR / f"{item.icon}@2x.png").exists(), item.icon
        assert (ICON_DIR / f"{item.icon}.svg").exists(), f"{item.icon} has no SVG source"
