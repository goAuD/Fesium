from fesium.core.project_detection import detect_project_profile, project_needs_php


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


def test_a_static_site_does_not_need_php(tmp_path):
    """A plain HTML and JavaScript project has no use for a PHP process."""
    (tmp_path / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "styles").mkdir()
    (tmp_path / "styles" / "main.css").write_text("body{}", encoding="utf-8")

    assert project_needs_php(tmp_path) is False
    assert detect_project_profile(tmp_path).needs_php is False


def test_laravel_needs_php(tmp_path):
    (tmp_path / "artisan").write_text("", encoding="utf-8")

    assert project_needs_php(tmp_path) is True
    assert detect_project_profile(tmp_path).needs_php is True


def test_a_composer_manifest_is_enough(tmp_path):
    (tmp_path / "composer.json").write_text("{}", encoding="utf-8")

    assert project_needs_php(tmp_path) is True


def test_a_php_file_below_the_root_counts(tmp_path):
    (tmp_path / "public").mkdir()
    (tmp_path / "public" / "index.php").write_text("<?php", encoding="utf-8")

    assert project_needs_php(tmp_path) is True


def test_the_scan_does_not_descend_into_dependency_folders(tmp_path):
    """A .php file inside node_modules says nothing about the project."""
    (tmp_path / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")
    buried = tmp_path / "node_modules" / "some-package"
    buried.mkdir(parents=True)
    (buried / "shipped.php").write_text("<?php", encoding="utf-8")

    assert project_needs_php(tmp_path) is False


def test_a_folder_too_large_to_judge_answers_php(tmp_path):
    """PHP serves static files too, so it is the answer that cannot break a site."""
    for index in range(30):
        (tmp_path / f"file_{index}.txt").write_text("x", encoding="utf-8")

    assert project_needs_php(tmp_path, entries=10) is True


def test_a_php_file_deeper_than_the_scan_is_missed_and_that_is_the_trade(tmp_path):
    """Documented on purpose: a full walk of a large folder took 6.4 seconds."""
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    (deep / "buried.php").write_text("<?php", encoding="utf-8")

    assert project_needs_php(tmp_path, depth=1) is False
