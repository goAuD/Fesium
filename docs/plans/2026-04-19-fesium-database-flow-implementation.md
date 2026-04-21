# Fesium Database Flow Implementation Plan

**Goal:** Restore the first real SQLite interaction workflow in `Fesium` with manual database selection, session-only read/write mode, one-statement SQL execution, clear result rendering, destructive-query confirmation, and a fix for the inset panel corner artifact.

**Architecture:** Keep the implementation inside the existing app/controller/core/view boundaries. The `FesiumController` owns database state and orchestration, `DatabaseManager` remains the execution engine, `DatabaseView` stays render-only with callbacks, and `bootstrap.py` handles file dialogs and confirmation dialogs. The inset-corner fix stays inside the reusable `PanelCard` widget so every inset panel benefits from the same rendering correction.

**Tech Stack:** Python 3.12, `pytest`, `customtkinter`, `tkinter.filedialog`, `tkinter.messagebox`, `sqlite3`, `pathlib`

---

## Current References

Read these before starting implementation:

- `docs/specs/2026-04-19-fesium-database-flow-design.md`
- `src/fesium/app/controller.py`
- `src/fesium/app/bootstrap.py`
- `src/fesium/core/database.py`
- `src/fesium/core/security.py`
- `src/fesium/core/project_detection.py`
- `src/fesium/ui/views/database_view.py`
- `src/fesium/ui/widgets/panel_card.py`
- `tests/unit/app/test_controller.py`
- `tests/unit/core/test_database.py`
- `tests/unit/core/test_security.py`
- `tests/unit/ui/test_database_view.py`
- `tests/unit/ui/test_panel_card.py`

## Guardrails

- Keep this milestone SQLite-only.
- Do not add schema browsing, table trees, or multi-statement execution.
- Keep `read-only` enabled on every app launch.
- Manual database selection must not be silently overwritten by project refresh.
- Keep the `DatabaseView` free of controller and `sqlite3` logic.
- Use a simple yes/no confirmation dialog for destructive queries in write mode.
- Fix the inset corner artifact in the shared `PanelCard` implementation, not with per-view hacks.

## Task 1: Extend Controller State for Database Workflow

**Files:**
- Modify: `src/fesium/app/controller.py`
- Modify: `tests/unit/app/test_controller.py`

**Step 1: Write failing controller tests for database defaults**

In `tests/unit/app/test_controller.py`, add:

```python
def test_controller_starts_with_database_read_only_enabled(tmp_path):
    controller = FesiumController(config=None, cwd=tmp_path)

    assert controller.state.database_path is None
    assert controller.state.database_source == "none"
    assert controller.state.database_read_only is True
    assert controller.state.database_last_query == ""
    assert controller.state.database_last_result == {"kind": "none"}
    assert controller.state.database_last_error == ""


def test_select_project_populates_project_database_when_detected(tmp_path, monkeypatch):
    project_dir = tmp_path / "demo-project"
    project_dir.mkdir()
    database_path = project_dir / "database.sqlite"
    database_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "fesium.app.controller.detect_project_profile",
        lambda path: ProjectProfile(
            root=project_dir.resolve(),
            kind="standard",
            document_root=project_dir.resolve(),
            database_path=database_path.resolve(),
        ),
    )
    monkeypatch.setattr(
        "fesium.app.controller.summarize_php_environment",
        lambda: EnvironmentStatus(php_available=False, php_version="", summary="PHP not found"),
    )
    monkeypatch.setattr(
        "fesium.app.controller.decide_runtime_backend",
        lambda profile, php_available: RuntimeDecision(backend_kind="static", reason="php_unavailable"),
    )

    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_project(project_dir)

    assert controller.state.database_path == database_path.resolve()
    assert controller.state.database_source == "project"
    assert controller.state.database_read_only is True
```

**Step 2: Run the controller tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
FAIL test_controller_starts_with_database_read_only_enabled
FAIL test_select_project_populates_project_database_when_detected
```

**Step 3: Add DB fields to `ControllerState` and initialize them**

In `src/fesium/app/controller.py`, extend `ControllerState` with:

```python
database_path: Path | None
database_source: str
database_read_only: bool
database_last_query: str
database_last_result: dict
database_last_error: str
```

Initialize them in `FesiumController.__init__()` as:

```python
database_path=None,
database_source="none",
database_read_only=True,
database_last_query="",
database_last_result={"kind": "none"},
database_last_error="",
```

In `select_project()`, after project detection:

- if `self.state.database_source != "manual"`:
  - set `database_path` to `profile.database_path`
  - set `database_source` to `"project"` when present, otherwise `"none"`
- always reset:
  - `database_read_only=True`
  - `database_last_query=""`
  - `database_last_result={"kind": "none"}`
  - `database_last_error=""`

This preserves manual DB selection while still rearming read-only mode for every new project selection.

**Step 4: Re-run the controller tests**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
all controller tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/app/controller.py tests/unit/app/test_controller.py
git commit -m "feat: add database state to Fesium controller"
```

## Task 2: Add Pure Query Validation Helpers

**Files:**
- Modify: `src/fesium/core/security.py`
- Modify: `tests/unit/core/test_security.py`

**Step 1: Write failing tests for empty and multi-statement rejection**

In `tests/unit/core/test_security.py`, add:

```python
from fesium.core.security import validate_single_sql_statement


def test_validate_single_sql_statement_rejects_empty_query():
    ok, message = validate_single_sql_statement("   ")
    assert ok is False
    assert "empty" in message.lower()


def test_validate_single_sql_statement_rejects_multiple_statements():
    ok, message = validate_single_sql_statement("SELECT 1; SELECT 2;")
    assert ok is False
    assert "single statement" in message.lower()


def test_validate_single_sql_statement_accepts_one_statement():
    ok, message = validate_single_sql_statement("SELECT 1")
    assert ok is True
    assert message == ""
```

**Step 2: Run the security tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/core/test_security.py -v
```

Expected output:

```text
E   ImportError: cannot import name 'validate_single_sql_statement'
```

**Step 3: Implement the pure validation helper**

In `src/fesium/core/security.py`, add:

```python
def validate_single_sql_statement(query: str) -> tuple[bool, str]:
    stripped = query.strip()
    if not stripped:
        return False, "Query is empty"

    statements = [segment.strip() for segment in stripped.split(";") if segment.strip()]
    if len(statements) != 1:
        return False, "Only a single SQL statement can be executed at a time"

    return True, ""
```

Keep this helper intentionally simple for the first milestone.

**Step 4: Re-run the security tests**

Run:

```bash
python -m pytest tests/unit/core/test_security.py -v
```

Expected output:

```text
all security tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/core/security.py tests/unit/core/test_security.py
git commit -m "feat: add single-statement SQL validation"
```

## Task 3: Add Database Selection and Query Execution Methods to the Controller

**Files:**
- Modify: `src/fesium/app/controller.py`
- Modify: `tests/unit/app/test_controller.py`

**Step 1: Write failing controller tests for manual DB selection and query execution**

In `tests/unit/app/test_controller.py`, add:

```python
def test_select_database_marks_manual_source_and_preserves_choice(tmp_path):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)

    controller.select_database(db_file)

    assert controller.state.database_path == db_file.resolve()
    assert controller.state.database_source == "manual"


def test_reset_to_project_database_restores_detected_database(tmp_path):
    project_db = tmp_path / "project.sqlite"
    project_db.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller._project_database_path = project_db.resolve()
    controller.state = controller.state.__class__(
        **{**controller.state.__dict__, "database_path": None, "database_source": "none"}
    )

    assert controller.reset_to_project_database() is True
    assert controller.state.database_path == project_db.resolve()
    assert controller.state.database_source == "project"


def test_run_database_query_blocks_write_query_in_read_only_mode(tmp_path):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_database(db_file)

    ok = controller.run_database_query("DELETE FROM users")

    assert ok is False
    assert controller.state.database_last_result["kind"] == "error"
    assert "Read-only mode" in controller.state.database_last_error


def test_run_database_query_stores_read_result(tmp_path, monkeypatch):
    db_file = tmp_path / "manual.sqlite"
    db_file.write_text("", encoding="utf-8")
    controller = FesiumController(config=None, cwd=tmp_path)
    controller.select_database(db_file)

    class FakeDatabaseManager:
        def __init__(self, db_path, read_only):
            assert read_only is True

        def execute(self, query, params=()):
            return True, {"columns": ["name"], "rows": [("Ada",)], "count": 1}

    monkeypatch.setattr("fesium.app.controller.DatabaseManager", FakeDatabaseManager)

    ok = controller.run_database_query("SELECT name FROM users")

    assert ok is True
    assert controller.state.database_last_result["kind"] == "read"
    assert controller.state.database_last_result["count"] == 1
    assert controller.state.database_last_error == ""
```

**Step 2: Run the controller tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
FAIL or ERROR in the new database controller tests
```

**Step 3: Implement controller-owned DB workflow**

In `src/fesium/app/controller.py`:

- import:

```python
from fesium.core.database import DatabaseManager, is_read_query
from fesium.core.security import classify_query_risk, validate_single_sql_statement
```

- add an internal project DB tracker:

```python
self._project_database_path: Path | None = None
```

- update `select_project()` to store:

```python
self._project_database_path = profile.database_path.resolve() if profile.database_path else None
```

- add:

```python
def select_database(self, path: Path) -> bool: ...
def reset_to_project_database(self) -> bool: ...
def set_database_read_only(self, enabled: bool) -> None: ...
def run_database_query(self, query: str) -> bool: ...
```

Implementation rules:

- `select_database(path)`:
  - resolve the file path
  - reject missing or non-file paths
  - set `database_path`, `database_source="manual"`
  - clear stale result and error state
- `reset_to_project_database()`:
  - return `False` if `_project_database_path` is missing
  - otherwise restore it and mark source `project`
- `set_database_read_only(enabled)`:
  - set `database_read_only` only for the current session
- `run_database_query(query)`:
  - store `database_last_query`
  - validate single statement
  - reject if no active `database_path`
  - reject write queries when read-only is on
  - execute with `DatabaseManager(str(self.state.database_path), read_only=self.state.database_read_only)`
  - normalize successful results into:
    - `{"kind": "read", ...}`
    - `{"kind": "write", ...}`
  - normalize failures into:
    - `{"kind": "error", "message": message}`

Do not handle the destructive confirmation in the controller; leave that decision to `bootstrap.py`.

**Step 4: Re-run the controller tests**

Run:

```bash
python -m pytest tests/unit/app/test_controller.py -v
```

Expected output:

```text
all controller tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/app/controller.py tests/unit/app/test_controller.py
git commit -m "feat: add controller-managed database workflow"
```

## Task 4: Expand the Database View Contract

**Files:**
- Modify: `src/fesium/ui/views/database_view.py`
- Modify: `tests/unit/ui/test_database_view.py`

**Step 1: Write failing view-model tests for the new DB summary**

In `tests/unit/ui/test_database_view.py`, replace or extend the tests with:

```python
from fesium.ui.views.database_view import build_database_summary, build_database_result_view_model


def test_build_database_summary_surfaces_manual_source_and_write_mode():
    summary = build_database_summary(
        db_path="D:/db/demo.sqlite",
        read_only=False,
        source="manual",
        project_database_available=True,
    )

    assert summary["source_badge"] == "Manual Database"
    assert summary["mode_badge"] == "Write Mode"
    assert summary["can_reset"] is True


def test_build_database_result_view_model_handles_read_results():
    model = build_database_result_view_model(
        {"kind": "read", "columns": ["name"], "rows": [("Ada",)], "count": 1},
        "",
    )

    assert model["title"] == "1 row"
    assert "Ada" in model["body"]


def test_build_database_result_view_model_prefers_explicit_error():
    model = build_database_result_view_model({"kind": "none"}, "Read-only mode: Write operations are disabled")
    assert model["tone"] == "accent.danger"
```

**Step 2: Run the DB view tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/ui/test_database_view.py -v
```

Expected output:

```text
FAIL or ERROR in the new database view tests
```

**Step 3: Implement the expanded `DatabaseView`**

In `src/fesium/ui/views/database_view.py`:

- update `build_database_summary()` to accept:

```python
db_path: str
read_only: bool
source: str
project_database_available: bool
```

- add a pure helper:

```python
def build_database_result_view_model(result: dict, last_error: str) -> dict[str, str]:
    ...
```

- expand `DatabaseView.__init__()` to accept:

```python
source: str
project_database_available: bool
last_query: str
last_result: dict
last_error: str
on_select_database=None
on_reset_project_database=None
on_toggle_read_only=None
on_run_sql=None
```

- render:
  - source badge
  - mode badge
  - `Select Database File` button
  - `Reset to Project Database` button
  - a `CTkSwitch` for read-only
  - a `CTkTextbox` for SQL input
  - a `Run SQL` button
  - a results panel

Keep the result rendering simple and text-first in this milestone. Do not build a table grid widget.

**Step 4: Re-run the DB view tests**

Run:

```bash
python -m pytest tests/unit/ui/test_database_view.py -v
```

Expected output:

```text
all database view tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/database_view.py tests/unit/ui/test_database_view.py
git commit -m "feat: add interactive database view state and result rendering"
```

## Task 5: Wire Database Actions in `bootstrap.py`

**Files:**
- Modify: `src/fesium/app/bootstrap.py`
- Modify: `tests/unit/test_app_bootstrap.py`

**Step 1: Write failing bootstrap tests for DB view replacement**

In `tests/unit/test_app_bootstrap.py`, add:

```python
def test_replace_runtime_views_rebuilds_database_view_with_controller_database_state(tmp_path):
    shell = FakeShell()
    config = FakeConfig({"port": 8000})
    controller = FakeController(
        database_path=tmp_path / "manual.sqlite",
        database_source="manual",
        database_read_only=False,
        database_last_query="SELECT 1",
        database_last_result={"kind": "read", "columns": ["1"], "rows": [(1,)], "count": 1},
        database_last_error="",
    )

    _replace_runtime_views(
        shell=shell,
        controller=controller,
        config=config,
        fallback_project=tmp_path,
        select_project_action=lambda: None,
        start_action=lambda: None,
        stop_action=lambda: None,
        restart_action=lambda: None,
        open_browser_action=lambda: None,
    )

    database_factory = shell.factories["database"]
    assert database_factory is not None
```

Adapt the fake shell/controller helpers in that test module as needed.

**Step 2: Run the bootstrap tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/test_app_bootstrap.py -v
```

Expected output:

```text
FAIL in the database-view bootstrap test
```

**Step 3: Wire file picker, confirmation dialog, and DB callbacks**

In `src/fesium/app/bootstrap.py`:

- import:

```python
from tkinter import filedialog, messagebox
from fesium.core.security import classify_query_risk
```

- remove `_build_database_manager()` if it no longer reflects controller-owned DB state
- update `_replace_runtime_views()` so `DatabaseView` receives DB state from `controller.state`
- add actions:

```python
def select_database_action() -> None: ...
def reset_project_database_action() -> None: ...
def toggle_database_read_only_action() -> None: ...
def run_sql_action(query: str) -> None: ...
```

Implementation rules:

- `select_database_action()`:
  - use `askopenfilename`
  - preferred filetypes should include `*.sqlite`, `*.db`, `*.db3`
  - if the user cancels, do nothing
  - otherwise call `controller.select_database(...)`
- `reset_project_database_action()`:
  - call `controller.reset_to_project_database()`
- `toggle_database_read_only_action()`:
  - invert the current controller state
- `run_sql_action(query)`:
  - trim and risk-classify first
  - if destructive and `database_read_only` is already `False`, show:

```python
messagebox.askyesno(
    "Confirm Destructive Query",
    "This query may modify or remove data. Do you want to continue?",
)
```

  - only continue when confirmed
  - then call `controller.run_database_query(query)`

Refresh runtime views after each DB action.

**Step 4: Re-run the bootstrap tests**

Run:

```bash
python -m pytest tests/unit/test_app_bootstrap.py -v
```

Expected output:

```text
all bootstrap tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/app/bootstrap.py tests/unit/test_app_bootstrap.py
git commit -m "feat: wire database actions into Fesium bootstrap"
```

## Task 6: Fix the Inset Panel Corner Artifact

**Files:**
- Modify: `src/fesium/ui/widgets/panel_card.py`
- Modify: `tests/unit/ui/test_panel_card.py`

**Step 1: Write a failing pure test for the inset geometry contract**

In `tests/unit/ui/test_panel_card.py`, add:

```python
from fesium.ui.widgets.panel_card import resolve_panel_surface, resolve_panel_inset_geometry


def test_resolve_panel_inset_geometry_keeps_inner_radius_smaller_than_outer():
    geometry = resolve_panel_inset_geometry("inset")
    assert geometry["padding"] >= 3
    assert geometry["inner_corner_radius"] < geometry["outer_corner_radius"]


def test_resolve_panel_inset_geometry_supports_strong_variant():
    geometry = resolve_panel_inset_geometry("inset_strong")
    assert geometry["padding"] >= 3
```

**Step 2: Run the panel-card tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/ui/test_panel_card.py -v
```

Expected output:

```text
E   ImportError: cannot import name 'resolve_panel_inset_geometry'
```

**Step 3: Implement the reusable corner-fix geometry helper**

In `src/fesium/ui/widgets/panel_card.py`:

- add a pure helper:

```python
def resolve_panel_inset_geometry(variant: str) -> dict[str, int]:
    geometry = {
        "inset": {"padding": 3, "outer_corner_radius": 16, "inner_corner_radius": 12},
        "inset_strong": {"padding": 4, "outer_corner_radius": 16, "inner_corner_radius": 11},
    }
    ...
```

- use this helper when creating the inner frame instead of the current fixed `padx=2`, `pady=2`, `corner_radius=14`

The goal is to leave a cleaner outer corner silhouette, not to create a heavier-looking inset.

**Step 4: Re-run the panel-card tests**

Run:

```bash
python -m pytest tests/unit/ui/test_panel_card.py -v
```

Expected output:

```text
all panel-card tests pass
```

**Step 5: Commit**

```bash
git add src/fesium/ui/widgets/panel_card.py tests/unit/ui/test_panel_card.py
git commit -m "fix: clean up inset panel corner rendering"
```

## Task 7: Update Public Docs and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Run: full verification commands

**Step 1: Update the public docs**

In `README.md`, update the feature summary so it mentions:

- manual SQLite database selection
- session-only read/write mode
- one-statement SQL execution
- destructive query confirmation

In `CHANGELOG.md`, add an `Unreleased` entry that summarizes:

- restored `Database` interactivity
- safety-preserving write-mode behavior
- the inset panel corner rendering fix

**Step 2: Run the full verification suite**

Run:

```bash
python -m pytest -v
python -m compileall src
python fesium.py
```

Expected output:

```text
all tests pass
compileall completes without errors
the desktop app opens and can be closed normally
```

During the manual app check, verify:

- `Select Database File` works
- `Reset to Project Database` only enables when a project DB exists
- `Read-only` starts enabled on app launch
- write queries are blocked while `read-only` is on
- destructive queries in write mode prompt for confirmation
- read query results render clearly
- inset panel corners render cleanly without visible chipping

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: document restored Fesium database workflow"
```

## Final Checkpoint

At the end of the milestone:

- `git status --short` should be clean
- full `pytest` should pass
- `compileall` should pass
- the app should be manually checked for DB execution, read-only behavior, and panel-corner rendering
- the milestone should remain SQLite-only and single-statement only
