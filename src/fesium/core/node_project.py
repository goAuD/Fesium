"""What a JavaScript project needs, read from its own package.json.

Fesium serves files. It does not build them, and it never will - that is a
different job and a much larger one. What it can do is stop pretending, and say
which command builds this project and where that command will serve it.

The case this was written for: a SvelteKit project opened in Fesium has no
index.html at its root, so the static server rendered a directory listing of
the repository. Nothing about that says "run npm run dev" - it looks like a
broken site, which is exactly the wall a student hits and cannot see over.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# 256KB is far more than any package.json needs and far less than a file that
# would be slow to read. A manifest larger than this is not one.
MAX_MANIFEST_BYTES = 256 * 1024

# Ordered: the first match wins, so a framework built on Vite is recognised as
# itself rather than as Vite. The port is the framework's own default, which is
# what the student will see in their terminal.
FRAMEWORKS = (
    ("@sveltejs/kit", "SvelteKit", 5173),
    ("next", "Next.js", 3000),
    ("nuxt", "Nuxt", 3000),
    ("astro", "Astro", 4321),
    ("@angular/core", "Angular", 4200),
    ("react-scripts", "Create React App", 3000),
    ("@vue/cli-service", "Vue CLI", 8080),
    ("vite", "Vite", 5173),
)

# Where these frameworks leave a build, in the order worth trying. A directory
# only counts when it has an index.html: an empty build/ means the build has
# not been run, and serving it would be the same confusion one level down.
BUILD_OUTPUTS = ("build", "dist", "out", ".output/public", ".svelte-kit/output/client")


@dataclass(frozen=True)
class NodeProject:
    """A JavaScript project, as far as its manifest admits to being one."""

    name: str
    framework: str
    dev_command: str
    dev_port: int | None
    build_command: str
    built_output: Path | None
    """A directory that already holds a built index.html, if there is one."""


def read_manifest(root: Path) -> dict | None:
    """Parse ``package.json``, or return None if there is not a usable one.

    Deliberately forgiving. A manifest that is missing, too large, not valid
    JSON or not an object simply means "this is not a Node project as far as
    Fesium is concerned" - never an error the user has to deal with.
    """
    manifest = Path(root) / "package.json"
    try:
        if not manifest.is_file() or manifest.stat().st_size > MAX_MANIFEST_BYTES:
            return None
        parsed = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _dependencies(manifest: dict) -> set[str]:
    names: set[str] = set()
    for key in ("dependencies", "devDependencies"):
        section = manifest.get(key)
        if isinstance(section, dict):
            names.update(section)
    return names


def find_built_output(root: Path) -> Path | None:
    """A directory that already holds a built ``index.html``."""
    for candidate in BUILD_OUTPUTS:
        directory = Path(root) / candidate
        if (directory / "index.html").is_file():
            return directory
    return None


def detect_node_project(root: Path) -> NodeProject | None:
    """Identify the JavaScript project at ``root``, if there is one."""
    manifest = read_manifest(root)
    if manifest is None:
        return None

    scripts = manifest.get("scripts")
    scripts = scripts if isinstance(scripts, dict) else {}
    dependencies = _dependencies(manifest)

    framework, port = "Node", None
    for package, label, default_port in FRAMEWORKS:
        if package in dependencies:
            framework, port = label, default_port
            break

    # The script the project actually declares beats the one the framework
    # usually uses: a project is free to call it "start" or "serve".
    dev_script = next((name for name in ("dev", "start", "serve") if name in scripts), "")
    build_script = next((name for name in ("build", "generate") if name in scripts), "")

    name = manifest.get("name")
    return NodeProject(
        name=name if isinstance(name, str) else "",
        framework=framework,
        dev_command=f"npm run {dev_script}" if dev_script else "",
        dev_port=port,
        build_command=f"npm run {build_script}" if build_script else "",
        built_output=find_built_output(root),
    )


def describe_node_project(project: NodeProject | None) -> list[str]:
    """What to tell someone whose project Fesium cannot serve as it stands.

    Imperative and specific. "This project needs a build step" is true and
    useless; the sentence a stuck student needs contains a command.
    """
    if project is None:
        return []

    lines = [
        f"This is a {project.framework} project. Fesium serves files, it does not "
        "build them, so there is nothing here to serve until a build has run."
    ]

    if project.built_output is not None:
        lines.append(
            f"It has already been built. Point Fesium at {project.built_output.name} "
            "and it will serve that.")
    elif project.build_command:
        lines.append(
            f"Run {project.build_command} first, then point Fesium at the folder "
            "it produces.")

    if project.dev_command:
        where = f" on port {project.dev_port}" if project.dev_port else ""
        lines.append(
            f"While you are working, run {project.dev_command} instead. It serves the "
            f"project itself{where} and rebuilds as you edit, which Fesium does not do.")

    lines.append("If npm is not installed yet, install Node.js first.")
    return lines
