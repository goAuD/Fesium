# Fesium Phase 1 Implementation Plan

**Goal:** Transform the current NanoServer repository into the first `Fesium` release: a modular `CustomTkinter` desktop app with a sidebar shell, offline-bundled fonts, security-first defaults, and a public-repo-ready structure.

**Architecture:** Keep the proven backend behavior from the current flat files, move it into `src/fesium/core/`, build a thin UI shell in `src/fesium/ui/`, and preserve a thin launcher at the repo root. Do not delete the legacy flat modules until the new package bootstraps, core tests pass, and the new launch path works end-to-end.

**Tech Stack:** Python 3.8+, `CustomTkinter`, `pytest`, `pathlib`, `sqlite3`, `subprocess`, `threading`

---

## Current References

Read these before starting implementation:

- `docs/specs/2026-04-17-fesium-redesign-design.md`
- `config.py`
- `database.py`
- `server.py`
- `nano_theme.py`
- `nanoserver.py`
- `test_nanoserver.py`

## Guardrails

- Keep the first release on `CustomTkinter`; do not introduce `PySide6`.
- Do not add internet dependencies to runtime behavior.
- Vendor fonts into the repo; do not load fonts from a CDN.
- Keep SQLite read-only mode enabled by default.
- Keep server binding local-only by default.
- Do not remove the legacy root files until Task 12.

## Task 1: Package Bootstrap and Repo Scaffold

**Files:**

- Create: `pyproject.toml`
- Create: `src/fesium/__init__.py`
- Create: `src/fesium/app.py`
- Create: `src/fesium/core/__init__.py`
- Create: `src/fesium/ui/__init__.py`
- Create: `src/fesium/assets/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/test_app_metadata.py`
- Modify: `.gitignore`

**Step 1: Write the failing bootstrap test**

In `tests/unit/test_app_metadata.py`:

```python
from fesium import __version__
from fesium.app import AppMetadata, build_window_title


def test_build_window_title_includes_brand_and_version():
    assert build_window_title("1.0.0") == "Fesium v1.0.0"


def test_app_metadata_defaults_to_fesium_brand():
    metadata = AppMetadata(name="Fesium", tagline="Local dev tools for students and developers")
    assert metadata.name == "Fesium"
    assert "students and developers" in metadata.tagline
    assert __version__ == "0.1.0"
```

**Step 2: Run the bootstrap test to verify it fails**

Run: `python -m pytest tests/unit/test_app_metadata.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium'
```

**Step 3: Implement the minimal package bootstrap**

In `tests/conftest.py`:

```python
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

In `src/fesium/__init__.py`:

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

In `src/fesium/app.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class AppMetadata:
    name: str
    tagline: str


def build_window_title(version: str) -> str:
    return f"Fesium v{version}"
```

In `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "fesium"
version = "0.1.0"
description = "Local dev tools for students and developers"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
  "customtkinter>=5.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Update `.gitignore` to include:

```gitignore
.fesium/
build/
dist/
```

**Step 4: Run the bootstrap test again**

Run: `python -m pytest tests/unit/test_app_metadata.py -v`

Expected output:

```text
tests/unit/test_app_metadata.py::test_build_window_title_includes_brand_and_version PASSED
tests/unit/test_app_metadata.py::test_app_metadata_defaults_to_fesium_brand PASSED
```

**Step 5: Commit**

```bash
git add pyproject.toml .gitignore src/fesium tests/conftest.py tests/unit/test_app_metadata.py
git commit -m "chore: bootstrap Fesium src package"
```

## Task 2: Config and Path Migration

**Files:**

- Create: `src/fesium/core/config.py`
- Create: `src/fesium/core/paths.py`
- Create: `tests/unit/core/test_config.py`
- Modify: `src/fesium/app.py`

**Step 1: Write failing tests for config storage and legacy path migration**

In `tests/unit/core/test_config.py`:

```python
from pathlib import Path

from fesium.core.config import Config
from fesium.core.paths import AppPaths


def test_app_paths_defaults_to_fesium_directory(tmp_path):
    paths = AppPaths(home_dir=tmp_path)
    assert paths.config_dir == tmp_path / ".fesium"


def test_config_roundtrip_uses_json_file(tmp_path):
    config = Config(config_dir=tmp_path / ".fesium")
    config.set("port", 9001)
    loaded = Config(config_dir=tmp_path / ".fesium")
    assert loaded.port == 9001


def test_config_prefers_legacy_directory_when_migrating(tmp_path):
    legacy_dir = tmp_path / ".nanoserver"
    legacy_dir.mkdir()
    (legacy_dir / "config.json").write_text('{"port": 8123}', encoding="utf-8")

    paths = AppPaths(home_dir=tmp_path)
    assert paths.legacy_config_dir == legacy_dir

    config = Config(config_dir=paths.config_dir, legacy_config_dir=paths.legacy_config_dir)
    assert config.port == 8123
```

**Step 2: Run the config test to verify it fails**

Run: `python -m pytest tests/unit/core/test_config.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.config'
```

**Step 3: Implement path helpers and config storage**

In `src/fesium/core/paths.py`:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    home_dir: Path

    @property
    def config_dir(self) -> Path:
        return self.home_dir / ".fesium"

    @property
    def legacy_config_dir(self) -> Path:
        return self.home_dir / ".nanoserver"
```

In `src/fesium/core/config.py`, port the existing JSON persistence from `config.py` and add legacy loading:

```python
import json
from pathlib import Path


class Config:
    DEFAULT_CONFIG = {
        "last_project": "",
        "port": 8000,
        "window_geometry": "1280x860",
        "active_view": "overview",
    }

    def __init__(self, config_dir: Path, legacy_config_dir: Path = None):
        self.config_dir = Path(config_dir)
        self.legacy_config_dir = Path(legacy_config_dir) if legacy_config_dir else None
        self.config_file = self.config_dir / "config.json"
        self._data = self.DEFAULT_CONFIG.copy()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        source = self.config_file
        if not source.exists() and self.legacy_config_dir:
            legacy_file = self.legacy_config_dir / "config.json"
            if legacy_file.exists():
                source = legacy_file
        if source.exists():
            self._data = {**self.DEFAULT_CONFIG, **json.loads(source.read_text(encoding="utf-8"))}
        return self._data

    def save(self):
        self.config_file.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    @property
    def port(self):
        return self._data["port"]
```

Update `src/fesium/app.py` to expose a helper:

```python
from pathlib import Path

from fesium.core.paths import AppPaths


def build_default_paths(home_dir: Path = None) -> AppPaths:
    return AppPaths(home_dir=home_dir or Path.home())
```

**Step 4: Run the config tests again**

Run: `python -m pytest tests/unit/core/test_config.py -v`

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/config.py src/fesium/core/paths.py src/fesium/app.py tests/unit/core/test_config.py
git commit -m "feat: add Fesium config and path helpers"
```

## Task 3: Database Core Migration

**Files:**

- Create: `src/fesium/core/database.py`
- Create: `tests/unit/core/test_database.py`
- Reference: `database.py`
- Reference: `test_nanoserver.py`

**Step 1: Write failing database tests**

In `tests/unit/core/test_database.py`:

```python
import os
import tempfile

from fesium.core.database import DatabaseManager, is_read_query, validate_table_name


def test_is_read_query_blocks_write_keywords():
    assert is_read_query("SELECT * FROM users") is True
    assert is_read_query("DELETE FROM users") is False


def test_validate_table_name_rejects_injection_shapes():
    assert validate_table_name("users") is True
    assert validate_table_name("drop;users") is False


def test_database_manager_read_only_mode_blocks_write_queries():
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as handle:
        db_path = handle.name

    try:
        db = DatabaseManager(db_path)
        ok, _ = db.execute("CREATE TABLE test (id INTEGER)")
        assert ok is True

        db.read_only = True
        ok, message = db.execute("INSERT INTO test VALUES (1)")
        assert ok is False
        assert "Read-only mode" in message
    finally:
        os.remove(db_path)
```

**Step 2: Run the database tests to verify they fail**

Run: `python -m pytest tests/unit/core/test_database.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.database'
```

**Step 3: Port the database module**

In `src/fesium/core/database.py`, port the current logic from `database.py` with only these first-pass changes:

- keep `is_read_query`
- keep `validate_table_name`
- keep `DatabaseManager.execute`, `list_tables`, and `get_table_info`
- set `read_only = True` by default in `__init__`
- keep return shape compatible with the current UI code

Use this constructor:

```python
class DatabaseManager:
    def __init__(self, db_path: str = None, read_only: bool = True):
        self.db_path = db_path
        self.read_only = read_only
```

**Step 4: Run the database tests again**

Run: `python -m pytest tests/unit/core/test_database.py -v`

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/database.py tests/unit/core/test_database.py
git commit -m "feat: migrate database core into Fesium package"
```

## Task 4: Server Core and Environment Diagnostics

**Files:**

- Create: `src/fesium/core/server.py`
- Create: `src/fesium/core/environment.py`
- Create: `tests/unit/core/test_server.py`
- Create: `tests/unit/core/test_environment.py`
- Reference: `server.py`

**Step 1: Write failing tests for server helpers**

In `tests/unit/core/test_server.py`:

```python
from fesium.core.server import find_available_port, is_port_in_use


def test_find_available_port_returns_value_in_range():
    port = find_available_port(50000, max_attempts=5)
    assert port is not None
    assert 50000 <= port < 50005


def test_is_port_in_use_returns_bool():
    assert isinstance(is_port_in_use(59999), bool)
```

In `tests/unit/core/test_environment.py`:

```python
from fesium.core.environment import summarize_php_environment


def test_summarize_php_environment_missing_php(monkeypatch):
    monkeypatch.setattr("fesium.core.environment.check_php_installed", lambda: False)
    status = summarize_php_environment()
    assert status.php_available is False
    assert "PHP not found" in status.summary
```

**Step 2: Run the new tests and verify they fail**

Run: `python -m pytest tests/unit/core/test_server.py tests/unit/core/test_environment.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.server'
```

**Step 3: Port the server module and add environment summaries**

In `src/fesium/core/server.py`, port the current `PHPServer`, `check_php_installed`, `is_port_in_use`, and `find_available_port` behavior from `server.py`.

In `src/fesium/core/environment.py`:

```python
from dataclasses import dataclass
import subprocess

from fesium.core.server import check_php_installed, get_subprocess_flags


@dataclass(frozen=True)
class EnvironmentStatus:
    php_available: bool
    php_version: str
    summary: str


def get_php_version() -> str:
    result = subprocess.run(
        ["php", "-v"],
        capture_output=True,
        text=True,
        **get_subprocess_flags(),
    )
    if result.returncode != 0 or not result.stdout:
        return ""
    return result.stdout.splitlines()[0]


def summarize_php_environment() -> EnvironmentStatus:
    if not check_php_installed():
        return EnvironmentStatus(False, "", "PHP not found in PATH")
    version = get_php_version()
    return EnvironmentStatus(True, version, version or "PHP available")
```

**Step 4: Run the tests again**

Run: `python -m pytest tests/unit/core/test_server.py tests/unit/core/test_environment.py -v`

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/server.py src/fesium/core/environment.py tests/unit/core/test_server.py tests/unit/core/test_environment.py
git commit -m "feat: migrate server core and add environment diagnostics"
```

## Task 5: Project Detection and Security Guards

**Files:**

- Create: `src/fesium/core/project_detection.py`
- Create: `src/fesium/core/security.py`
- Create: `tests/unit/core/test_project_detection.py`
- Create: `tests/unit/core/test_security.py`

**Step 1: Write failing tests for project detection and dangerous query classification**

In `tests/unit/core/test_project_detection.py`:

```python
from pathlib import Path

from fesium.core.project_detection import detect_project_profile


def test_detect_project_profile_for_laravel(tmp_path):
    (tmp_path / "artisan").write_text("", encoding="utf-8")
    (tmp_path / "public").mkdir()
    profile = detect_project_profile(tmp_path)
    assert profile.kind == "laravel"
    assert profile.document_root == tmp_path / "public"
```

In `tests/unit/core/test_security.py`:

```python
from fesium.core.security import classify_query_risk, normalize_existing_directory


def test_classify_query_risk_marks_drop_as_destructive():
    risk = classify_query_risk("DROP TABLE users")
    assert risk.level == "danger"
    assert risk.requires_confirmation is True


def test_normalize_existing_directory_rejects_missing_path(tmp_path):
    missing = tmp_path / "does-not-exist"
    ok, result = normalize_existing_directory(missing)
    assert ok is False
    assert "does not exist" in result
```

**Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/unit/core/test_project_detection.py tests/unit/core/test_security.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.core.project_detection'
```

**Step 3: Implement profile and security helpers**

In `src/fesium/core/project_detection.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ProjectProfile:
    root: Path
    kind: str
    document_root: Path
    database_path: Optional[Path]


def detect_project_profile(root: Path) -> ProjectProfile:
    root = Path(root).resolve()
    if (root / "artisan").exists():
        database_path = root / "database" / "database.sqlite"
        return ProjectProfile(root, "laravel", root / "public", database_path if database_path.exists() else None)
    database_path = root / "database.sqlite"
    return ProjectProfile(root, "standard", root, database_path if database_path.exists() else None)
```

In `src/fesium/core/security.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union


@dataclass(frozen=True)
class QueryRisk:
    level: str
    requires_confirmation: bool
    first_word: str


def classify_query_risk(query: str) -> QueryRisk:
    first_word = query.lstrip("; \t\n").split()[0].upper() if query.strip() else ""
    destructive = {"DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE"}
    return QueryRisk(
        level="danger" if first_word in destructive else "safe",
        requires_confirmation=first_word in destructive,
        first_word=first_word,
    )


def normalize_existing_directory(pathlike) -> Tuple[bool, Union[str, Path]]:
    candidate = Path(pathlike).expanduser().resolve()
    if not candidate.exists():
        return False, f"Path does not exist: {candidate}"
    if not candidate.is_dir():
        return False, f"Path is not a directory: {candidate}"
    return True, candidate
```

**Step 4: Run the tests again**

Run: `python -m pytest tests/unit/core/test_project_detection.py tests/unit/core/test_security.py -v`

Expected output:

```text
4 passed
```

**Step 5: Commit**

```bash
git add src/fesium/core/project_detection.py src/fesium/core/security.py tests/unit/core/test_project_detection.py tests/unit/core/test_security.py
git commit -m "feat: add project detection and security guard helpers"
```

## Task 6: Theme Tokens and Offline Font Assets

**Files:**

- Create: `src/fesium/ui/theme/tokens.py`
- Create: `src/fesium/ui/theme/styles.py`
- Create: `src/fesium/assets/fonts/font_manifest.py`
- Create: `src/fesium/assets/fonts/README.md`
- Create: `src/fesium/assets/fonts/LICENSES.md`
- Add binary assets: `src/fesium/assets/fonts/Sora-SemiBold.ttf`
- Add binary assets: `src/fesium/assets/fonts/IBMPlexSans-Regular.ttf`
- Add binary assets: `src/fesium/assets/fonts/IBMPlexSans-Medium.ttf`
- Add binary assets: `src/fesium/assets/fonts/JetBrainsMono-Regular.ttf`
- Create: `tests/unit/ui/test_theme_tokens.py`

**Step 1: Write failing tests for theme token coverage and local font paths**

In `tests/unit/ui/test_theme_tokens.py`:

```python
from fesium.assets.fonts.font_manifest import FONT_FILES
from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS


def test_graphite_grid_color_tokens_include_required_keys():
    required = {
        "bg.app",
        "bg.sidebar",
        "bg.panel",
        "text.primary",
        "accent.primary",
        "accent.success",
        "accent.warning",
        "accent.danger",
    }
    assert required.issubset(COLOR_TOKENS.keys())


def test_font_manifest_points_to_local_files():
    assert FONT_FILES["heading"].name == "Sora-SemiBold.ttf"
    assert FONT_FILES["body"].name == "IBMPlexSans-Regular.ttf"
    assert FONT_FILES["mono"].name == "JetBrainsMono-Regular.ttf"
```

**Step 2: Run the theme tests and verify they fail**

Run: `python -m pytest tests/unit/ui/test_theme_tokens.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.ui.theme.tokens'
```

**Step 3: Implement theme tokens and font manifest**

In `src/fesium/ui/theme/tokens.py`:

```python
COLOR_TOKENS = {
    "bg.app": "#121419",
    "bg.sidebar": "#171a21",
    "bg.panel": "#181d25",
    "bg.panel_alt": "#151a22",
    "border.default": "#2b3440",
    "border.soft": "#29313d",
    "text.primary": "#eef3f7",
    "text.secondary": "#8f9aa8",
    "accent.primary": "#73F0FF",
    "accent.success": "#52E38F",
    "accent.warning": "#FFB454",
    "accent.danger": "#FF6B6B",
}

FONT_TOKENS = {
    "heading": ("Sora", 22, "bold"),
    "body": ("IBM Plex Sans", 13),
    "mono": ("JetBrains Mono", 12),
}
```

In `src/fesium/assets/fonts/font_manifest.py`:

```python
from pathlib import Path


FONT_DIR = Path(__file__).resolve().parent

FONT_FILES = {
    "heading": FONT_DIR / "Sora-SemiBold.ttf",
    "body": FONT_DIR / "IBMPlexSans-Regular.ttf",
    "body_medium": FONT_DIR / "IBMPlexSans-Medium.ttf",
    "mono": FONT_DIR / "JetBrainsMono-Regular.ttf",
}
```

In `src/fesium/assets/fonts/README.md`, record the exact upstream font package names and why they are vendored. In `src/fesium/assets/fonts/LICENSES.md`, record the license for each vendored font.

In `src/fesium/ui/theme/styles.py`, add a thin wrapper:

```python
import customtkinter as ctk


def apply_graphite_grid_theme() -> None:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
```

**Step 4: Vendor the binary font files**

Copy these exact files into `src/fesium/assets/fonts/` and commit them:

- `Sora-SemiBold.ttf`
- `IBMPlexSans-Regular.ttf`
- `IBMPlexSans-Medium.ttf`
- `JetBrainsMono-Regular.ttf`

Do not reference a CDN or external URL in runtime code.

**Step 5: Run the theme tests again**

Run: `python -m pytest tests/unit/ui/test_theme_tokens.py -v`

Expected output:

```text
2 passed
```

**Step 6: Commit**

```bash
git add src/fesium/ui/theme src/fesium/assets/fonts tests/unit/ui/test_theme_tokens.py
git commit -m "feat: add Graphite Grid tokens and bundled fonts"
```

## Task 7: Navigation Model and Shell Skeleton

**Files:**

- Create: `src/fesium/ui/navigation.py`
- Create: `src/fesium/ui/shell.py`
- Create: `src/fesium/ui/widgets/panel_card.py`
- Create: `src/fesium/ui/widgets/status_badge.py`
- Create: `tests/unit/ui/test_navigation.py`

**Step 1: Write failing tests for navigation order**

In `tests/unit/ui/test_navigation.py`:

```python
from fesium.ui.navigation import build_navigation_items


def test_navigation_matches_design_spec():
    items = build_navigation_items()
    assert [item.id for item in items] == [
        "overview",
        "server",
        "database",
        "environment",
        "settings",
    ]
```

**Step 2: Run the navigation test and verify it fails**

Run: `python -m pytest tests/unit/ui/test_navigation.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.ui.navigation'
```

**Step 3: Implement navigation data and a shell frame**

In `src/fesium/ui/navigation.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationItem:
    id: str
    label: str
    description: str


def build_navigation_items():
    return [
        NavigationItem("overview", "Overview", "Workspace, health, and quick actions"),
        NavigationItem("server", "Server", "Serve the current project locally"),
        NavigationItem("database", "Database", "SQLite queries with safety defaults"),
        NavigationItem("environment", "Environment", "Local toolchain diagnostics"),
        NavigationItem("settings", "Settings", "Preferences and defaults"),
    ]
```

In `src/fesium/ui/shell.py`, create a `FesiumShell(ctk.CTk)` class with:

- a sidebar frame
- a content frame
- a `set_active_view(view_id: str)` method
- a `register_view(view_id: str, factory)` method

Keep it minimal; the task is to establish layout, not to finish every view.

**Step 4: Run the navigation test again**

Run: `python -m pytest tests/unit/ui/test_navigation.py -v`

Expected output:

```text
1 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/navigation.py src/fesium/ui/shell.py src/fesium/ui/widgets/panel_card.py src/fesium/ui/widgets/status_badge.py tests/unit/ui/test_navigation.py
git commit -m "feat: add sidebar navigation and shell scaffold"
```

## Task 8: Overview and Server Views

**Files:**

- Create: `src/fesium/ui/views/overview_view.py`
- Create: `src/fesium/ui/views/server_view.py`
- Create: `tests/unit/ui/test_overview_view.py`
- Create: `tests/unit/ui/test_server_view.py`

**Step 1: Write failing tests for overview and server view models**

In `tests/unit/ui/test_overview_view.py`:

```python
from pathlib import Path

from fesium.core.project_detection import ProjectProfile
from fesium.ui.views.overview_view import build_overview_cards


def test_build_overview_cards_surfaces_workspace_and_health():
    profile = ProjectProfile(Path("D:/site"), "standard", Path("D:/site"), None)
    cards = build_overview_cards(profile, php_summary="PHP 8.4.0", server_running=False)
    assert "Workspace" in cards[0]["title"]
    assert any(card["title"] == "Environment Health" for card in cards)
```

In `tests/unit/ui/test_server_view.py`:

```python
from pathlib import Path

from fesium.ui.views.server_view import build_server_status


def test_build_server_status_reports_running_state():
    status = build_server_status(Path("D:/site/public"), 8000, True)
    assert status["label"] == "Running"
    assert status["url"] == "http://localhost:8000"
```

**Step 2: Run the view tests and verify they fail**

Run: `python -m pytest tests/unit/ui/test_overview_view.py tests/unit/ui/test_server_view.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.ui.views.overview_view'
```

**Step 3: Implement pure view-model helpers and thin view classes**

In `src/fesium/ui/views/overview_view.py`:

```python
def build_overview_cards(project_profile, php_summary: str, server_running: bool):
    return [
        {"title": "Workspace", "value": str(project_profile.root), "badge": project_profile.kind.title()},
        {"title": "Quick Actions", "value": "Start local server", "badge": "Ready" if not server_running else "Running"},
        {"title": "Environment Health", "value": php_summary, "badge": "Healthy" if php_summary else "Missing"},
    ]
```

In `src/fesium/ui/views/server_view.py`:

```python
def build_server_status(document_root, port: int, is_running: bool):
    return {
        "label": "Running" if is_running else "Stopped",
        "document_root": str(document_root),
        "url": f"http://localhost:{port}",
    }
```

Add minimal `OverviewView` and `ServerView` classes that render from these helpers rather than burying logic in widget callbacks.

**Step 4: Run the tests again**

Run: `python -m pytest tests/unit/ui/test_overview_view.py tests/unit/ui/test_server_view.py -v`

Expected output:

```text
2 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/overview_view.py src/fesium/ui/views/server_view.py tests/unit/ui/test_overview_view.py tests/unit/ui/test_server_view.py
git commit -m "feat: add overview and server views"
```

## Task 9: Database, Environment, and Settings Views

**Files:**

- Create: `src/fesium/ui/views/database_view.py`
- Create: `src/fesium/ui/views/environment_view.py`
- Create: `src/fesium/ui/views/settings_view.py`
- Create: `tests/unit/ui/test_database_view.py`
- Create: `tests/unit/ui/test_environment_view.py`
- Create: `tests/unit/ui/test_settings_view.py`

**Step 1: Write failing tests for the remaining view helpers**

In `tests/unit/ui/test_database_view.py`:

```python
from fesium.ui.views.database_view import build_database_summary


def test_build_database_summary_surfaces_read_only_badge():
    summary = build_database_summary("D:/site/database.sqlite", True)
    assert summary["badge"] == "Read-only Enabled"
```

In `tests/unit/ui/test_environment_view.py`:

```python
from fesium.core.environment import EnvironmentStatus
from fesium.ui.views.environment_view import build_environment_rows


def test_build_environment_rows_contains_php_summary():
    rows = build_environment_rows(EnvironmentStatus(True, "PHP 8.4.0", "PHP 8.4.0"))
    assert rows[0]["label"] == "PHP"
```

In `tests/unit/ui/test_settings_view.py`:

```python
from fesium.ui.views.settings_view import build_settings_rows


def test_build_settings_rows_contains_default_port():
    rows = build_settings_rows({"port": 8000, "active_view": "overview"})
    assert any(row["label"] == "Default Port" for row in rows)
```

**Step 2: Run the tests and verify they fail**

Run: `python -m pytest tests/unit/ui/test_database_view.py tests/unit/ui/test_environment_view.py tests/unit/ui/test_settings_view.py -v`

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.ui.views.database_view'
```

**Step 3: Implement the remaining view helpers and thin views**

In `src/fesium/ui/views/database_view.py`:

```python
def build_database_summary(db_path: str, read_only: bool):
    return {
        "path": db_path or "No database selected",
        "badge": "Read-only Enabled" if read_only else "Write Mode",
    }
```

In `src/fesium/ui/views/environment_view.py`:

```python
def build_environment_rows(status):
    return [
        {"label": "PHP", "value": status.summary},
        {"label": "Version", "value": status.php_version or "Unavailable"},
    ]
```

In `src/fesium/ui/views/settings_view.py`:

```python
def build_settings_rows(config_data: dict):
    return [
        {"label": "Default Port", "value": str(config_data.get("port", 8000))},
        {"label": "Last Active View", "value": config_data.get("active_view", "overview")},
    ]
```

**Step 4: Run the tests again**

Run: `python -m pytest tests/unit/ui/test_database_view.py tests/unit/ui/test_environment_view.py tests/unit/ui/test_settings_view.py -v`

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/database_view.py src/fesium/ui/views/environment_view.py src/fesium/ui/views/settings_view.py tests/unit/ui/test_database_view.py tests/unit/ui/test_environment_view.py tests/unit/ui/test_settings_view.py
git commit -m "feat: add database environment and settings views"
```

## Task 10: App Orchestration and Thin Launchers

**Files:**

- Modify: `src/fesium/app.py`
- Create: `fesium.py`
- Modify: `nanoserver.py`
- Create: `tests/unit/test_app_bootstrap.py`

**Step 1: Write failing tests for app context bootstrapping**

In `tests/unit/test_app_bootstrap.py`:

```python
from pathlib import Path

from fesium.app import build_app_context


def test_build_app_context_uses_last_project_or_cwd(tmp_path):
    context = build_app_context(
        cwd=tmp_path,
        config_data={"last_project": ""},
    )
    assert context.project_root == tmp_path
    assert context.active_view == "overview"
```

**Step 2: Run the bootstrap test and verify it fails**

Run: `python -m pytest tests/unit/test_app_bootstrap.py -v`

Expected output:

```text
E   ImportError: cannot import name 'build_app_context' from 'fesium.app'
```

**Step 3: Implement app context wiring and launchers**

In `src/fesium/app.py`, add:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppContext:
    project_root: Path
    active_view: str


def build_app_context(cwd: Path, config_data: dict) -> AppContext:
    project_root = Path(config_data.get("last_project") or cwd).resolve()
    active_view = config_data.get("active_view", "overview")
    return AppContext(project_root=project_root, active_view=active_view)
```

Then add a `main()` function that:

- loads `Config`
- builds `AppPaths`
- detects project profile
- creates `PHPServer`, `DatabaseManager`, and `EnvironmentStatus`
- instantiates `FesiumShell`
- registers the five real views
- runs `mainloop()`

Create `fesium.py` as the primary root launcher:

```python
from fesium.app import main


if __name__ == "__main__":
    main()
```

Change `nanoserver.py` into a temporary compatibility shim:

```python
from fesium.app import main


if __name__ == "__main__":
    main()
```

Do not leave the old `CustomTkinter` monolith in place after this task.

**Step 4: Run the bootstrap test again**

Run: `python -m pytest tests/unit/test_app_bootstrap.py -v`

Expected output:

```text
1 passed
```

**Step 5: Run a non-GUI bootstrap smoke test**

Run: `python -c "from pathlib import Path; from fesium.app import build_app_context; print(build_app_context(Path.cwd(), {'last_project': '', 'active_view': 'overview'}).active_view)"`

Expected output:

```text
overview
```

**Step 6: Commit**

```bash
git add src/fesium/app.py fesium.py nanoserver.py tests/unit/test_app_bootstrap.py
git commit -m "feat: wire Fesium app bootstrap and launchers"
```

## Task 11: Public Repo Files and Contributor Guidance

**Files:**

- Create: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `.editorconfig`
- Create: `.github/workflows/python-tests.yml`
- Create: `tests/unit/test_repo_contract.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.gitignore`

**Step 1: Write failing repo contract tests**

In `tests/unit/test_repo_contract.py`:

```python
from pathlib import Path


def test_required_repo_files_exist():
    for relative in [
        "AGENTS.md",
        "CONTRIBUTING.md",
        ".editorconfig",
        ".github/workflows/python-tests.yml",
    ]:
        assert Path(relative).exists(), relative


def test_readme_mentions_fesium():
    content = Path("README.md").read_text(encoding="utf-8")
    assert "Fesium" in content
```

**Step 2: Run the repo contract test and verify it fails**

Run: `python -m pytest tests/unit/test_repo_contract.py -v`

Expected output:

```text
FAILED tests/unit/test_repo_contract.py::test_required_repo_files_exist - AssertionError: AGENTS.md
```

**Step 3: Add the repo files**

`AGENTS.md` must document:

- `Fesium` as an offline-first local dev toolbox
- `Graphite Grid` as the approved visual direction
- bundled fonts only
- `src/` package layout
- security-first defaults
- no new god files
- update docs/specs/decisions with major changes

`CONTRIBUTING.md` must explain:

- Python setup
- `pip install -r requirements-dev.txt`
- `python -m pytest -v`
- where new code belongs under `src/fesium/`

`.editorconfig` should include:

```ini
root = true

[*.py]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 4
insert_final_newline = true
```

`.github/workflows/python-tests.yml` should:

- run on `push` and `pull_request`
- install Python 3.11
- install `requirements.txt` and `requirements-dev.txt`
- run `python -m pytest -v`

Update `README.md` to rename the project to `Fesium` and explain the first-release scope honestly. Update `CHANGELOG.md` with an unreleased entry for the rebrand and restructure.

**Step 4: Run the repo contract test again**

Run: `python -m pytest tests/unit/test_repo_contract.py -v`

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add AGENTS.md CONTRIBUTING.md .editorconfig .github/workflows/python-tests.yml README.md CHANGELOG.md .gitignore tests/unit/test_repo_contract.py
git commit -m "docs: add Fesium repo guidance and CI"
```

## Task 12: Legacy Cleanup and Full Verification

**Files:**

- Delete: `config.py`
- Delete: `database.py`
- Delete: `server.py`
- Delete: `nano_theme.py`
- Delete: `test_nanoserver.py`
- Modify: `requirements.txt`
- Modify: `requirements-dev.txt`

**Step 1: Write a final migration safety test**

Create `tests/unit/test_import_contract.py`:

```python
def test_root_launcher_imports_new_package():
    import fesium  # noqa: F401
    from fesium.app import main  # noqa: F401
```

**Step 2: Run the import contract test and verify it passes before deleting legacy files**

Run: `python -m pytest tests/unit/test_import_contract.py -v`

Expected output:

```text
1 passed
```

**Step 3: Delete legacy flat modules and old all-in-one test file**

Remove:

- `config.py`
- `database.py`
- `server.py`
- `nano_theme.py`
- `test_nanoserver.py`

Only do this after all new-package tests already pass.

**Step 4: Run the full test suite**

Run: `python -m pytest -v`

Expected output:

```text
... PASSED
=== X passed in Ys ===
```

The exact count will vary, but there must be zero failures and zero import errors.

**Step 5: Run a compile check**

Run: `python -m compileall src`

Expected output:

```text
Listing 'src'...
Compiling 'src/fesium/app.py'...
```

**Step 6: Optional manual smoke test**

Run: `python fesium.py`

Expected result:

- app window opens
- sidebar shows the five real views
- no network access is required
- start/stop flow still works when PHP is installed

**Step 7: Commit**

```bash
git add -A
git commit -m "refactor: complete Fesium phase 1 migration"
```
