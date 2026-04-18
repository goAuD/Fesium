from fesium.core.project_detection import detect_project_profile


def test_detect_project_profile_for_laravel(tmp_path):
    (tmp_path / "artisan").write_text("", encoding="utf-8")
    (tmp_path / "public").mkdir()

    profile = detect_project_profile(tmp_path)

    assert profile.kind == "laravel"
    assert profile.document_root == tmp_path / "public"


def test_detect_project_profile_for_standard_project(tmp_path):
    profile = detect_project_profile(tmp_path)

    assert profile.kind == "standard"
    assert profile.document_root == tmp_path
    assert profile.database_path is None
