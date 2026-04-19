from fesium.ui.widgets.scrollable_view_body import resolve_scrollable_view_body_style


def test_scrollable_view_body_uses_app_background():
    style = resolve_scrollable_view_body_style()
    assert style["fg_color"] == "transparent"
    assert style["scrollbar_fg"] == "bg.app"
    assert style["scrollbar_button"] == "bg.panel"
