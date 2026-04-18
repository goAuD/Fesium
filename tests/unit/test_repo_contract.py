from pathlib import Path


def test_required_repo_files_exist():
    for relative in [
        "AGENTS.md",
        "CONTRIBUTING.md",
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
