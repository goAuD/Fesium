from pathlib import Path


def test_required_repo_files_exist():
    for relative in [
        "AGENTS.md",
        "CONTRIBUTING.md",
        "LICENSE",
        ".editorconfig",
        ".github/workflows/python-tests.yml",
    ]:
        assert Path(relative).exists(), relative


def test_gitignore_blocks_local_superpowers_artifacts():
    content = Path(".gitignore").read_text(encoding="utf-8")
    assert ".superpowers/" in content


def test_readme_mentions_fesium():
    content = Path("README.md").read_text(encoding="utf-8")
    assert "Fesium" in content


def test_license_surface_mentions_apache():
    readme = Path("README.md").read_text(encoding="utf-8")
    license_text = Path("LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in readme
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
