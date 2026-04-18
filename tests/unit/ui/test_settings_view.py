from fesium.ui.views.settings_view import build_settings_rows


def test_build_settings_rows_contains_default_port():
    rows = build_settings_rows({"port": 8000, "active_view": "overview"})

    assert any(row["label"] == "Default Port" for row in rows)
