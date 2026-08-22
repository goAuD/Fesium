import json

import pytest

from fesium.core.node_project import (
    NodeProject,
    describe_node_project,
    detect_node_project,
    find_built_output,
    read_manifest,
)


def make_project(root, manifest, **files):
    root.mkdir(parents=True, exist_ok=True)
    (root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    for name, content in files.items():
        target = root / name.replace("__", "/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


# -- the manifest ------------------------------------------------------------

def test_a_folder_without_a_manifest_is_not_a_node_project(tmp_path):
    assert detect_node_project(tmp_path) is None


@pytest.mark.parametrize("content", ["{ not json", "[]", '"a string"', ""])
def test_an_unusable_manifest_is_not_an_error(tmp_path, content):
    """A broken package.json means "not a Node project", never a crash.

    This runs on project selection, where anything that raises would stop the
    user opening their folder at all.
    """
    (tmp_path / "package.json").write_text(content, encoding="utf-8")

    assert read_manifest(tmp_path) is None
    assert detect_node_project(tmp_path) is None


def test_an_enormous_manifest_is_ignored_rather_than_read(tmp_path):
    (tmp_path / "package.json").write_text("{" + " " * (300 * 1024) + "}", encoding="utf-8")

    assert read_manifest(tmp_path) is None


# -- frameworks --------------------------------------------------------------

@pytest.mark.parametrize("package,expected,port", [
    ("@sveltejs/kit", "SvelteKit", 5173),
    ("next", "Next.js", 3000),
    ("astro", "Astro", 4321),
    ("@angular/core", "Angular", 4200),
    ("react-scripts", "Create React App", 3000),
    ("vite", "Vite", 5173),
])
def test_the_framework_is_read_from_the_dependencies(tmp_path, package, expected, port):
    make_project(tmp_path / "app", {
        "name": "app", "scripts": {"dev": "x", "build": "y"},
        "devDependencies": {package: "^1.0.0"}})

    project = detect_node_project(tmp_path / "app")

    assert (project.framework, project.dev_port) == (expected, port)


def test_a_framework_beats_the_bundler_it_is_built_on(tmp_path):
    """SvelteKit projects depend on Vite too, and are not Vite projects."""
    make_project(tmp_path / "app", {
        "name": "app", "scripts": {"dev": "vite dev"},
        "devDependencies": {"vite": "^5.0.0", "@sveltejs/kit": "^2.0.0"}})

    assert detect_node_project(tmp_path / "app").framework == "SvelteKit"


def test_a_plain_node_project_is_still_recognised(tmp_path):
    make_project(tmp_path / "app", {"name": "app", "scripts": {"start": "node ."}})

    project = detect_node_project(tmp_path / "app")

    assert project.framework == "Node"
    assert project.dev_command == "npm run start"
    assert project.dev_port is None


def test_the_declared_script_wins_over_the_conventional_one(tmp_path):
    """A project is free to call it serve rather than dev."""
    make_project(tmp_path / "app", {
        "name": "app", "scripts": {"serve": "vite"},
        "devDependencies": {"vite": "^5.0.0"}})

    assert detect_node_project(tmp_path / "app").dev_command == "npm run serve"


# -- a build that already exists ---------------------------------------------

def test_a_built_output_is_found_when_it_holds_an_index(tmp_path):
    root = make_project(tmp_path / "app", {"name": "app"})
    (root / "build").mkdir()
    (root / "build" / "index.html").write_text("<!doctype html>", encoding="utf-8")

    assert find_built_output(root).name == "build"


def test_an_empty_build_directory_does_not_count(tmp_path):
    """An empty build/ means the build has not run.

    Serving it would put the same "nothing here" one level down, which is
    worse than saying so plainly.
    """
    root = make_project(tmp_path / "app", {"name": "app"})
    (root / "build").mkdir()

    assert find_built_output(root) is None


# -- the advice --------------------------------------------------------------

def test_nothing_is_said_about_a_project_that_is_not_node():
    assert describe_node_project(None) == []


def test_the_advice_contains_the_command_and_the_port():
    """"This project needs a build step" is true and useless."""
    advice = " ".join(describe_node_project(
        NodeProject("app", "SvelteKit", "npm run dev", 5173, "npm run build", None)))

    assert "npm run build" in advice
    assert "npm run dev" in advice
    assert "5173" in advice


def test_an_already_built_project_is_pointed_at_its_output(tmp_path):
    root = make_project(tmp_path / "app", {
        "name": "app", "scripts": {"build": "vite build"},
        "devDependencies": {"vite": "^5.0.0"}})
    (root / "dist").mkdir()
    (root / "dist" / "index.html").write_text("<!doctype html>", encoding="utf-8")

    advice = " ".join(describe_node_project(detect_node_project(root)))

    assert "already been built" in advice
    assert "dist" in advice
    assert "Run npm run build first" not in advice
