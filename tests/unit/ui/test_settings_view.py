from fesium.ui.views.settings_view import build_settings_placeholder


def test_build_settings_placeholder_is_honest_about_missing_controls():
    placeholder = build_settings_placeholder({"port": 8000, "active_view": "overview"})

    assert placeholder["title"] == "No in-app settings yet"
    assert "removed" in placeholder["body"]
    assert "read-only mode" in placeholder["footnote"]
