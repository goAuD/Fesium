from fesium.ui.navigation import build_navigation_items


def test_navigation_matches_design_spec():
    items = build_navigation_items()
    assert [item.id for item in items] == [
        "overview",
        "server",
        "database",
        "environment",
        "settings",
    ]
