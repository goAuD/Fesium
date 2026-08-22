import re
from pathlib import Path


def test_requirements_txt_contains_runtime_and_test_dependencies():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert "customtkinter" in requirements
    assert "pytest" in requirements


def test_legacy_requirements_dev_file_is_removed():
    assert Path("requirements-dev.txt").exists() is False


def test_repo_docs_install_from_requirements_txt():
    readme = Path("README.md").read_text(encoding="utf-8")
    setup_doc = Path("docs/dev/setup.md").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/python-tests.yml").read_text(encoding="utf-8")

    assert "python -m pip install -r requirements.txt" in readme
    assert "python -m pip install -r requirements.txt" in setup_doc
    assert "python -m pip install -r requirements.txt" in workflow


def _declared_minimum_python() -> str:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'requires-python = ">=([\d.]+)"', pyproject)
    assert match, "pyproject.toml must declare requires-python"
    return match.group(1)


def test_ci_runs_the_minimum_python_version_the_project_claims():
    """An untested floor is a guess.

    The repo claimed 3.8 for a long time while CI only ever ran 3.11 and 3.12,
    so nobody noticed that `X | None` annotations need 3.10 at import time.
    """
    workflow = Path(".github/workflows/python-tests.yml").read_text(encoding="utf-8")

    assert f'"{_declared_minimum_python()}"' in workflow


def test_docs_quote_the_same_minimum_python_version():
    minimum = _declared_minimum_python()
    readme = Path("README.md").read_text(encoding="utf-8")
    setup_doc = Path("docs/dev/setup.md").read_text(encoding="utf-8")

    assert f"Python {minimum}" in readme
    assert f"Python {minimum}" in setup_doc


def _requirement_lines() -> list[str]:
    text = Path("requirements.txt").read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def test_every_requirement_is_pinned_to_an_exact_version():
    """Semgrep skips any dependency that is not pinned.

    It was skipping all of them, so 17751 supply-chain rules ran against zero
    packages and no dependency was ever checked for a known vulnerability.
    """
    unpinned = [line for line in _requirement_lines() if "==" not in line]

    assert unpinned == []


def test_pyproject_keeps_ranges_rather_than_pins():
    """The two files have different jobs.

    pyproject declares what the package needs in order to work, so it stays
    abstract; requirements declares what an install actually gets.
    """
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "customtkinter>=" in pyproject
    assert "customtkinter==" not in pyproject


def test_dependabot_keeps_the_pins_current():
    """A pin with no update path is how a project freezes on a bad version."""
    dependabot = Path(".github/dependabot.yml").read_text(encoding="utf-8")

    assert "package-ecosystem: pip" in dependabot
    assert "package-ecosystem: github-actions" in dependabot
