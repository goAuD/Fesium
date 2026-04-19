# Fesium Server Flow Implementation Plan

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Restore the first real interactive server workflow inside the new `Fesium` shell: project selection, automatic runtime detection, `Start` / `Stop` / `Restart` / `Open in Browser`, and a real server log panel.

**Architecture:** Keep the UI view layer thin and move the new interaction logic into a dedicated controller plus small core helpers. Because the repository currently has `src/fesium/app.py` as a single module, first convert that module into an `src/fesium/app/` package so `controller.py` can exist cleanly under it. The milestone uses `PHPServer` when PHP exists and a new static fallback server when it does not.

**Tech Stack:** Python 3.12, `pytest`, `customtkinter`, `pathlib`, `threading`, `subprocess`, `http.server`, `socketserver`, `webbrowser`, `tkinter.filedialog`

---

## Current References

Read these before starting implementation:

- `docs/superpowers/specs/2026-04-19-fesium-server-flow-design.md`
- `src/fesium/app.py`
- `src/fesium/core/project_detection.py`
- `src/fesium/core/server.py`
- `src/fesium/ui/shell.py`
- `src/fesium/ui/views/overview_view.py`
- `src/fesium/ui/views/server_view.py`
- `tests/unit/test_app_bootstrap.py`
- `tests/unit/ui/test_overview_view.py`
- `tests/unit/ui/test_server_view.py`

## Guardrails

- Do not wire database interaction in this milestone.
- Keep `Overview` informational only. Do not add live control buttons there.
- Keep `Start`, `Stop`, `Restart`, and `Open in Browser` in the `Server` view only.
- Keep SQLite read-only defaults untouched.
- Keep all runtime serving local-first on `localhost`.
- Use the standard library for the static fallback server.
- Avoid turning `controller.py` into a second monolith. Push backend-specific logic down into `core/`.
- Update `README.md` and `CHANGELOG.md` when the new interactive flow lands.

## Task 1: Convert `fesium.app` From Module to Package

**Files:**
- Delete: `src/fesium/app.py`
- Create: `src/fesium/app/__init__.py`
- Create: `src/fesium/app/bootstrap.py`
- Modify: `fesium.py`
- Modify: `nanoserver.py`
- Modify: `tests/unit/test_app_bootstrap.py`
- Modify: `tests/unit/test_app_metadata.py`

**Step 1: Extend the bootstrap import contract**

In `tests/unit/test_app_bootstrap.py`, add:

```python
from fesium.app import build_app_context, build_default_paths, main


def test_fesium_app_package_exports_bootstrap_symbols():
    assert callable(build_app_context)
    assert callable(build_default_paths)
    assert callable(main)
```

**Step 2: Run the bootstrap tests to verify the current structure does not yet support package expansion**

Run:

```bash
python -m pytest tests/unit/test_app_bootstrap.py tests/unit/test_app_metadata.py -v
```

Expected output:

```text
PASSED
```

This should still pass before the refactor. The point is to lock the public import surface before changing file layout.

**Step 3: Convert `src/fesium/app.py` into a package**

- Create `src/fesium/app/__init__.py`
- Move the current bootstrap logic into `src/fesium/app/bootstrap.py`
- Re-export the public symbols from `src/fesium/app/__init__.py`
- Delete `src/fesium/app.py`

Use this package surface in `src/fesium/app/__init__.py`:

```python
from .bootstrap import AppContext, AppMetadata, build_app_context, build_default_paths, build_window_title, main

__all__ = [
    "AppContext",
    "AppMetadata",
    "build_app_context",
    "build_default_paths",
    "build_window_title",
    "main",
]
```

Leave the actual runtime body in `bootstrap.py` unchanged for now, except for import path fixes.

**Step 4: Keep root launchers compatible**

In `fesium.py`, keep:

```python
def main():
    return importlib.import_module("fesium.app").main()
```

In `nanoserver.py`, keep:

```python
from fesium.app import main
```

No behavior change yet. This task is only about making room for `controller.py`.

**Step 5: Run bootstrap tests again**

Run:

```bash
python -m pytest tests/unit/test_app_bootstrap.py tests/unit/test_app_metadata.py -v
```

Expected output:

```text
3 passed
```

**Step 6: Commit**

```bash
git add src/fesium/app/__init__.py src/fesium/app/bootstrap.py src/fesium/app.py fesium.py nanoserver.py tests/unit/test_app_bootstrap.py tests/unit/test_app_metadata.py
git commit -m "refactor: convert fesium app bootstrap into package"
```

## Task 2: Runtime Detection and Browser Helper

**Files:**
- Create: `src/fesium/core/runtime_detection.py`
- Create: `src/fesium/core/browser.py`
- Create: `tests/unit/core/test_runtime_detection.py`
- Create: `tests/unit/core/test_browser.py`

**Step 1: Write the failing core tests**

In `tests/unit/core/test_runtime_detection.py`:

```python
from pathlib import Path

from fesium.core.project_detection import ProjectProfile
from fesium.core.runtime_detection import RuntimeDecision, decide_runtime_backend


def test_decide_runtime_backend_prefers_php_when_available():
    profile = ProjectProfile(
        root=Path("C:/Projects/demo"),
        kind="standard",
        document_root=Path("C:/Projects/demo"),
        database_path=None,
    )

    decision = decide_runtime_backend(profile, php_available=True)

    assert isinstance(decision, RuntimeDecision)
    assert decision.backend_kind == "php"


def test_decide_runtime_backend_falls_back_to_static_without_php():
    profile = ProjectProfile(
        root=Path("C:/Projects/demo"),
        kind="standard",
        document_root=Path("C:/Projects/demo"),
        database_path=None,
    )

    decision = decide_runtime_backend(profile, php_available=False)

    assert decision.backend_kind == "static"
    assert decision.reason == "php_unavailable"
```

In `tests/unit/core/test_browser.py`:

```python
from fesium.core.browser import open_local_url


def test_open_local_url_rejects_empty_urls(monkeypatch):
    called = []
    monkeypatch.setattr("fesium.core.browser.webbrowser.open", lambda url: called.append(url))

    assert open_local_url("") is False
    assert called == []


def test_open_local_url_opens_valid_localhost_url(monkeypatch):
    called = []
    monkeypatch.setattr("fesium.core.browser.webbrowser.open", lambda url: called.append(url) or True)

    assert open_local_url("http://localhost:8000") is True
    assert called == ["http://localhost:8000"]
```

**Step 2: Run the new tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/core/test_runtime_detection.py tests/unit/core/test_browser.py -v
```

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.runtime_detection'
E   ModuleNotFoundError: No module named 'fesium.core.browser'
```

**Step 3: Implement the new core helpers**

In `src/fesium/core/runtime_detection.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDecision:
    backend_kind: str
    reason: str


def decide_runtime_backend(profile, php_available: bool) -> RuntimeDecision:
    if php_available:
        return RuntimeDecision(backend_kind="php", reason="php_available")

    return RuntimeDecision(backend_kind="static", reason="php_unavailable")
```

In `src/fesium/core/browser.py`:

```python
import webbrowser


def open_local_url(url: str) -> bool:
    if not url:
        return False
    if not url.startswith("http://localhost:") and not url.startswith("http://127.0.0.1:"):
        return False
    return bool(webbrowser.open(url))
```

Keep this task intentionally narrow. Do not add controller logic here.

**Step 4: Run the tests again**

Run:

```bash
python -m pytest tests/unit/core/test_runtime_detection.py tests/unit/core/test_browser.py -v
```

Expected output:

```text
4 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/runtime_detection.py src/fesium/core/browser.py tests/unit/core/test_runtime_detection.py tests/unit/core/test_browser.py
git commit -m "feat: add runtime detection and browser helpers"
```

## Task 3: Static Fallback Server Core

**Files:**
- Create: `src/fesium/core/static_server.py`
- Create: `tests/unit/core/test_static_server.py`

**Step 1: Write the failing static-server tests**

In `tests/unit/core/test_static_server.py`:

```python
from pathlib import Path

from fesium.core.static_server import StaticServer


def test_static_server_starts_and_exposes_local_url(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    logs = []
    server = StaticServer(on_log=logs.append)

    url = server.start(document_root=project, port=8123)

    assert url == "http://localhost:8123"
    assert server.is_running is True
    assert any("Started" in line for line in logs)

    server.stop()


def test_static_server_stop_marks_server_not_running(tmp_path):
    project = tmp_path / "site"
    project.mkdir()
    (project / "index.html").write_text("<h1>hello</h1>", encoding="utf-8")

    server = StaticServer()
    server.start(document_root=project, port=8124)
    server.stop()

    assert server.is_running is False
```

**Step 2: Run the static-server tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/core/test_static_server.py -v
```

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.static_server'
```

**Step 3: Implement a minimal static fallback server**

In `src/fesium/core/static_server.py`, implement:

- a `StaticServer` class
- `start(document_root: Path, port: int) -> str`
- `stop() -> None`
- `is_running` property
- shared `on_log` callback

Recommended structure:

```python
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading


class StaticServer:
    def __init__(self, on_log=None):
        self.on_log = on_log or (lambda message: None)
        self._httpd = None
        self._thread = None
        self.port = None
        self.document_root = None

    @property
    def is_running(self) -> bool:
        return self._httpd is not None

    def start(self, document_root: Path, port: int) -> str:
        handler = partial(SimpleHTTPRequestHandler, directory=str(document_root))
        self._httpd = ThreadingHTTPServer(("localhost", port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.port = port
        self.document_root = Path(document_root)
        self.on_log(f"[Fesium] Started static server at http://localhost:{port}")
        return f"http://localhost:{port}"

    def stop(self) -> None:
        if not self._httpd:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        self._httpd = None
        self.on_log("[Fesium] Static server stopped")
```

Use `ThreadingHTTPServer`. Do not add custom request logging yet.

**Step 4: Run the static-server tests again**

Run:

```bash
python -m pytest tests/unit/core/test_static_server.py -v
```

Expected output:

```text
2 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/static_server.py tests/unit/core/test_static_server.py
git commit -m "feat: add static fallback server core"
```

## Task 4: Controller State Model and Log Buffer

**Files:**
- Create: `src/fesium/app/controller.py`
- Create: `tests/unit/app/test_controller.py`

**Step 1: Write the failing controller-state tests**

In `tests/unit/app/test_controller.py`:

```python
from pathlib import Path

from fesium.app.controller import FesiumController


def test_controller_starts_with_stopped_state(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    state = controller.state

    assert state.server_status == "stopped"
    assert state.backend_kind == "none"
    assert state.log_lines == []


def test_controller_log_buffer_is_bounded(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path, log_limit=3)

    controller.append_log("one")
    controller.append_log("two")
    controller.append_log("three")
    controller.append_log("four")

    assert controller.state.log_lines == ["two", "three", "four"]
```

**Step 2: Run the controller tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.app.controller'
```

**Step 3: Implement the controller state shell**

In `src/fesium/app/controller.py`:

```python
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class ControllerState:
    project_root: Path | None
    project_kind: str
    document_root: Path | None
    backend_kind: str
    server_status: str
    local_url: str
    php_available: bool
    last_error: str
    log_lines: list[str]


class FesiumController:
    def __init__(self, config, cwd: Path, log_limit: int = 200):
        self.config = config
        self.cwd = Path(cwd)
        self.log_limit = log_limit
        self.state = ControllerState(
            project_root=None,
            project_kind="unknown",
            document_root=None,
            backend_kind="none",
            server_status="stopped",
            local_url="",
            php_available=False,
            last_error="",
            log_lines=[],
        )

    def append_log(self, message: str) -> None:
        next_lines = [*self.state.log_lines, message][-self.log_limit :]
        self.state = replace(self.state, log_lines=next_lines)
```

Do not add runtime wiring yet.

**Step 4: Run the controller tests again**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
2 passed
```

**Step 5: Commit**

```bash
git add src/fesium/app/controller.py tests/unit/app/test_controller.py
git commit -m "feat: add Fesium controller state shell"
```

## Task 5: Project Selection and Backend Resolution in Controller

**Files:**
- Modify: `src/fesium/app/controller.py`
- Modify: `tests/unit/app/test_controller.py`

**Step 1: Extend the failing controller tests**

Append to `tests/unit/app/test_controller.py`:

```python
from fesium.core.project_detection import ProjectProfile
from fesium.core.runtime_detection import RuntimeDecision


def test_select_project_updates_project_and_backend_state(tmp_path, monkeypatch):
    controller = FesiumController(config=None, cwd=tmp_path)
    project = tmp_path / "demo"
    project.mkdir()

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda root: ProjectProfile(root=project, kind="standard", document_root=project, database_path=None),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: type("Env", (), {"php_available": False, "summary": "PHP not found", "php_version": ""})(),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(backend_kind="static", reason="php_unavailable"),
    )

    controller.select_project(project)

    assert controller.state.project_root == project
    assert controller.state.project_kind == "standard"
    assert controller.state.document_root == project
    assert controller.state.backend_kind == "static"
    assert controller.state.php_available is False
```

**Step 2: Run the controller tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
FAILED tests/unit/app/test_controller.py::test_select_project_updates_project_and_backend_state - AttributeError
```

**Step 3: Implement project selection**

In `src/fesium/app/controller.py`:

- import `detect_project_profile`
- import `summarize_php_environment`
- import `decide_runtime_backend`
- add `select_project(path: Path) -> None`

Recommended implementation shape:

```python
def select_project(self, path: Path) -> None:
    project_root = Path(path).resolve()
    profile = detect_project_profile(project_root)
    environment = summarize_php_environment()
    decision = decide_runtime_backend(profile, php_available=environment.php_available)

    self.state = replace(
        self.state,
        project_root=profile.root,
        project_kind=profile.kind,
        document_root=profile.document_root,
        backend_kind=decision.backend_kind,
        php_available=environment.php_available,
        last_error="",
    )
    self.append_log(f"[Fesium] Project selected: {profile.root}")
    self.append_log(f"[Fesium] Backend: {decision.backend_kind}")

    if self.config is not None:
        self.config.set("last_project", str(profile.root))
```

Do not start any backend yet.

**Step 4: Run the controller tests again**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/app/controller.py tests/unit/app/test_controller.py
git commit -m "feat: add controller project selection and runtime resolution"
```

## Task 6: Controller Start/Stop/Restart/Open Actions

**Files:**
- Modify: `src/fesium/app/controller.py`
- Modify: `tests/unit/app/test_controller.py`

**Step 1: Extend the failing controller action tests**

Append to `tests/unit/app/test_controller.py`:

```python
def test_start_moves_controller_to_running(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.state = controller.state.__class__(
        project_root=tmp_path,
        project_kind="standard",
        document_root=tmp_path,
        backend_kind="static",
        server_status="stopped",
        local_url="",
        php_available=False,
        last_error="",
        log_lines=[],
    )

    class FakeBackend:
        is_running = False
        def start(self, document_root, port):
            self.is_running = True
            return "http://localhost:8000"
        def stop(self):
            self.is_running = False

    controller._backend = FakeBackend()
    controller.start()

    assert controller.state.server_status == "running"
    assert controller.state.local_url == "http://localhost:8000"


def test_restart_is_rejected_while_stopped(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert controller.restart() is False
    assert controller.state.server_status == "stopped"


def test_open_in_browser_is_rejected_without_running_server(tmp_path, monkeypatch):
    controller = FesiumController(config=None, cwd=tmp_path)
    called = []
    monkeypatch.setattr("fesium.app.controller.open_local_url", lambda url: called.append(url))

    assert controller.open_in_browser() is False
    assert called == []
```

**Step 2: Run the controller tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
FAILED tests/unit/app/test_controller.py::test_start_moves_controller_to_running
FAILED tests/unit/app/test_controller.py::test_restart_is_rejected_while_stopped
FAILED tests/unit/app/test_controller.py::test_open_in_browser_is_rejected_without_running_server
```

**Step 3: Implement controller actions**

In `src/fesium/app/controller.py`:

- add `_backend` field
- add `start`, `stop`, `restart`, and `open_in_browser`
- add a small `_build_backend` helper that returns:
  - `PHPServer(on_log=self.append_log)` when `backend_kind == "php"`
  - `StaticServer(on_log=self.append_log)` when `backend_kind == "static"`

Recommended `start` shape:

```python
def start(self) -> bool:
    if not self.state.document_root:
        self.state = replace(self.state, server_status="error", last_error="No project selected")
        self.append_log("[Fesium] ERROR: No project selected")
        return False

    if self._backend is None:
        self._backend = self._build_backend()

    url = self._backend.start(self.state.document_root, self._resolve_port())
    self.state = replace(self.state, server_status="running", local_url=url, last_error="")
    return True
```

Recommended `restart` rule:

```python
def restart(self) -> bool:
    if self.state.server_status != "running":
        self.append_log("[Fesium] Restart rejected: server not running")
        return False
    self.stop()
    return self.start()
```

Keep `open_in_browser` guarded:

```python
def open_in_browser(self) -> bool:
    if self.state.server_status != "running" or not self.state.local_url:
        self.append_log("[Fesium] Open in Browser rejected: server not running")
        return False
    return open_local_url(self.state.local_url)
```

**Step 4: Run the controller tests again**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
6 passed
```

**Step 5: Commit**

```bash
git add src/fesium/app/controller.py tests/unit/app/test_controller.py
git commit -m "feat: add controller server action flow"
```

## Task 7: Server View State Helpers and Control Surface

**Files:**
- Modify: `src/fesium/ui/views/server_view.py`
- Modify: `tests/unit/ui/test_server_view.py`

**Step 1: Replace the simple status helper with a state-driven view model test**

In `tests/unit/ui/test_server_view.py`, replace the current test with:

```python
from pathlib import Path

from fesium.ui.views.server_view import build_server_view_model


def test_build_server_view_model_exposes_button_guards():
    model = build_server_view_model(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        document_root=Path("C:/Projects/demo"),
        backend_kind="static",
        server_status="stopped",
        local_url="",
        last_error="",
    )

    assert model["status_label"] == "Stopped"
    assert model["backend_label"] == "Static Fallback"
    assert model["actions"]["start"] is True
    assert model["actions"]["stop"] is False
    assert model["actions"]["restart"] is False
    assert model["actions"]["open_in_browser"] is False
```

**Step 2: Run the server-view test to verify it fails**

Run:

```bash
python -m pytest tests/unit/ui/test_server_view.py -v
```

Expected output:

```text
FAILED tests/unit/ui/test_server_view.py::test_build_server_view_model_exposes_button_guards - ImportError
```

**Step 3: Implement a proper server-view helper**

In `src/fesium/ui/views/server_view.py`:

- add `build_server_view_model(...)`
- keep the labels state-driven
- add button-enable booleans
- render:
  - selected project
  - project type
  - document root
  - backend label
  - local URL
  - status

Add placeholders for the actual button callbacks:

```python
self.select_project_button = ctk.CTkButton(...)
self.start_button = ctk.CTkButton(...)
self.stop_button = ctk.CTkButton(...)
self.restart_button = ctk.CTkButton(...)
self.open_browser_button = ctk.CTkButton(...)
```

Do not wire commands yet. This task only builds the UI surface and helper model.

**Step 4: Run the server-view test again**

Run:

```bash
python -m pytest tests/unit/ui/test_server_view.py -v
```

Expected output:

```text
1 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/server_view.py tests/unit/ui/test_server_view.py
git commit -m "feat: add state-driven server view surface"
```

## Task 8: Overview Live Summary From Controller State

**Files:**
- Modify: `src/fesium/ui/views/overview_view.py`
- Modify: `tests/unit/ui/test_overview_view.py`

**Step 1: Update the overview helper test**

In `tests/unit/ui/test_overview_view.py`, change the helper test to use explicit state fields:

```python
from pathlib import Path

from fesium.ui.views.overview_view import build_overview_cards


def test_build_overview_cards_surfaces_workspace_and_health():
    cards = build_overview_cards(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        php_summary="PHP 8.3.7 (cli)",
        server_status="running",
        local_url="http://localhost:8000",
    )

    assert cards[0]["title"] == "Workspace"
    assert cards[0]["value"] == "C:/Projects/demo"
    assert cards[1]["badge"] == "Running"
    assert "http://localhost:8000" in cards[1]["value"]
```

**Step 2: Run the overview-view test to verify it fails**

Run:

```bash
python -m pytest tests/unit/ui/test_overview_view.py -v
```

Expected output:

```text
FAILED tests/unit/ui/test_overview_view.py::test_build_overview_cards_surfaces_workspace_and_health - TypeError
```

**Step 3: Update the overview helper and view**

In `src/fesium/ui/views/overview_view.py`:

- make `build_overview_cards(...)` take primitive state fields instead of the whole project profile object
- use `server_status` and `local_url` to render the quick-action card
- keep `Overview` button-free

Recommended quick-action value:

```python
"Open the Server view to manage the active site" if server_status != "running" else f"Running at {local_url}"
```

**Step 4: Run the overview-view test again**

Run:

```bash
python -m pytest tests/unit/ui/test_overview_view.py -v
```

Expected output:

```text
1 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/overview_view.py tests/unit/ui/test_overview_view.py
git commit -m "feat: reflect live server state in overview view"
```

## Task 9: Wire Controller, Dialog, Actions, and Log Panel Into the App

**Files:**
- Modify: `src/fesium/app/bootstrap.py`
- Modify: `src/fesium/app/controller.py`
- Modify: `src/fesium/ui/views/server_view.py`
- Modify: `src/fesium/ui/shell.py`
- Modify: `tests/unit/test_app_bootstrap.py`

**Step 1: Add the failing integration-level bootstrap contract**

Append to `tests/unit/test_app_bootstrap.py`:

```python
from fesium.app.controller import FesiumController


def test_build_app_context_preserves_last_project(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": str(tmp_path / "demo"), "active_view": "server"},
    )

    assert context.project_root == (tmp_path / "demo").resolve()
    assert context.active_view == "server"
```

This test should already pass. It is a regression guard before rewiring the app bootstrap.

**Step 2: Wire the app runtime**

In `src/fesium/app/bootstrap.py`:

- create one `FesiumController`
- call `controller.select_project(...)` during startup using:
  - `context.project_root` when it exists
  - otherwise `Path.cwd()`
- pass controller-backed state into `OverviewView` and `ServerView`
- on close:
  - persist `window_geometry`
  - persist `active_view`
  - stop the active backend through the controller

In `src/fesium/ui/views/server_view.py`:

- add optional command parameters:
  - `on_select_project`
  - `on_start`
  - `on_stop`
  - `on_restart`
  - `on_open_browser`
- bind those callbacks to the buttons
- add a log display widget such as `CTkTextbox`
- render controller log lines into that widget

Use `tkinter.filedialog.askdirectory()` inside the bootstrap/controller wiring layer, not inside a core module.

**Step 3: Keep view refresh logic explicit**

Do not invent a large event bus in this milestone.

Use a simple refresh strategy:

- store the controller in bootstrap scope
- rebuild or refresh the active `Overview` and `Server` views after each server action
- keep `Database`, `Environment`, and `Settings` untouched except for compatible imports

If needed, add a small helper in `shell.py` to replace an existing registered view with a fresh factory output.

**Step 4: Run the focused tests and full unit suite**

Run:

```bash
python -m pytest tests/unit/test_app_bootstrap.py tests/unit/app/test_controller.py tests/unit/ui/test_server_view.py tests/unit/ui/test_overview_view.py -v
python -m pytest tests/unit -v
```

Expected output:

```text
... PASSED
=== 52+ passed in X.XXs ===
```

The exact total may increase. Zero failures is the requirement.

**Step 5: Commit**

```bash
git add src/fesium/app/bootstrap.py src/fesium/app/controller.py src/fesium/ui/views/server_view.py src/fesium/ui/views/overview_view.py src/fesium/ui/shell.py tests/unit/test_app_bootstrap.py
git commit -m "feat: wire server flow into Fesium shell"
```

## Task 10: Documentation Update and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Step 1: Update the README**

Add or update short user-facing copy so the README now states that `Fesium` can:

- select a local project folder
- auto-detect a Laravel or standard project
- run with PHP when available
- fall back to static serving when PHP is unavailable
- open the running local site in the browser

Do not claim database editing is complete.

**Step 2: Update the changelog**

Add a new unreleased entry describing:

- server interaction flow restored
- static fallback server added
- controller-based runtime orchestration added
- live server log panel added

Do not create a new tag or release in this task.

**Step 3: Run final verification**

Run:

```bash
python -m pytest -v
python -m compileall src
python fesium.py
```

Expected results:

- full test suite passes
- compile check succeeds
- the desktop app launches
- from the `Server` view you can:
  - choose a project folder
  - start the server
  - stop the server
  - restart the server
  - open the site in a browser

**Step 4: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: document restored Fesium server workflow"
```
