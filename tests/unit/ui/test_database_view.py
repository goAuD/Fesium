from fesium.ui.views.database_view import build_database_summary


def test_build_database_summary_surfaces_read_only_badge():
    summary = build_database_summary("D:/site/database.sqlite", True)

    assert summary["badge"] == "Read-only Enabled"
