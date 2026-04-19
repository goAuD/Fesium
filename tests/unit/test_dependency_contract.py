from pathlib import Path


def test_requirements_txt_contains_runtime_and_test_dependencies():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert "customtkinter" in requirements
    assert "pytest" in requirements


def test_requirements_dev_txt_is_only_a_compatibility_shim():
    requirements_dev = Path("requirements-dev.txt").read_text(encoding="utf-8").strip()
    assert requirements_dev == "-r requirements.txt"


def test_repo_docs_install_from_requirements_txt():
    readme = Path("README.md").read_text(encoding="utf-8")
    contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/python-tests.yml").read_text(encoding="utf-8")

    assert "python -m pip install -r requirements.txt" in readme
    assert "python -m pip install -r requirements.txt" in contributing
    assert "python -m pip install -r requirements.txt" in workflow
