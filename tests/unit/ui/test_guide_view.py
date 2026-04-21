from fesium.ui.views.guide_view import build_guide_sections


def test_build_guide_sections_mentions_static_projects_as_a_valid_fit():
    sections = build_guide_sections()

    assert any(section["title"] == "Static Hosting Matters" for section in sections)
    assert any("plain HTML" in section["body"] for section in sections)
