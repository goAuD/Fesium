# Fesium Shell Density Implementation Plan

**Goal:** Improve the default desktop usability of the current `Fesium` shell through a moderate window-size bump, larger baseline typography, scroll-safe content bodies, responsive `Server` controls, and inset-style panel surfaces.

**Architecture:** Keep this milestone inside the existing UI layer. The shell remains a thin frame, `PanelCard` becomes the reusable depth primitive, and a small scroll-body widget is introduced so `Server`, `Database`, `Environment`, and `Settings` do not each invent their own scroll behavior. `Overview` stays status-first and should not be turned into an operational surface.

**Tech Stack:** Python 3.12, `pytest`, `customtkinter`, `tkinter`, `pathlib`

---

## Current References

Read these before starting implementation:

- `docs/specs/2026-04-19-fesium-shell-density-design.md`
- `src/fesium/ui/shell.py`
- `src/fesium/ui/theme/tokens.py`
- `src/fesium/ui/widgets/panel_card.py`
- `src/fesium/ui/views/server_view.py`
- `src/fesium/ui/views/database_view.py`
- `src/fesium/ui/views/environment_view.py`
- `src/fesium/ui/views/settings_view.py`
- `tests/unit/ui/test_theme_tokens.py`
- `tests/unit/ui/test_server_view.py`
- `tests/unit/ui/test_database_view.py`
- `tests/unit/ui/test_environment_view.py`
- `tests/unit/ui/test_settings_view.py`

## Guardrails

- Do not change the restored server-flow behavior in this milestone.
- Do not add new operational buttons to `Overview`.
- Keep the sidebar fixed and the shell itself simple.
- Use content scrolling to absorb overflow instead of assuming the user will resize the whole window.
- Do not solve `Server` clipping only by enlarging the shell; the control layout must also degrade cleanly.
- Keep panel styling aligned with the current Graphite Grid palette.
- Do not stage or overwrite `docs/assets/screenshots/fesium-overview.png` unless the user explicitly asks for it.

## Task 1: Lock the New Shell Baseline and Type Ramp

**Files:**
- Create: `tests/unit/ui/test_shell.py`
- Modify: `tests/unit/ui/test_theme_tokens.py`
- Modify: `src/fesium/ui/shell.py`
- Modify: `src/fesium/ui/theme/tokens.py`

**Step 1: Add failing tests for the new geometry and font sizes**

In `tests/unit/ui/test_shell.py`, add:

```python
from fesium.ui.shell import DEFAULT_WINDOW_GEOMETRY, MIN_WINDOW_SIZE


def test_shell_uses_desktop_density_default_geometry():
    assert DEFAULT_WINDOW_GEOMETRY == "1400x960"


def test_shell_uses_desktop_density_minimum_size():
    assert MIN_WINDOW_SIZE == (1100, 760)
```

In `tests/unit/ui/test_theme_tokens.py`, add:

```python
def test_font_tokens_match_shell_density_scale():
    assert FONT_TOKENS["heading"] == ("Sora", 24, "bold")
    assert FONT_TOKENS["body"] == ("IBM Plex Sans", 14)
    assert FONT_TOKENS["body_medium"] == ("IBM Plex Sans", 14)
    assert FONT_TOKENS["mono"] == ("JetBrains Mono", 13)
```

**Step 2: Run the targeted tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/ui/test_shell.py tests/unit/ui/test_theme_tokens.py -v
```

Expected output:

```text
FAIL tests/unit/ui/test_shell.py::test_shell_uses_desktop_density_default_geometry
FAIL tests/unit/ui/test_shell.py::test_shell_uses_desktop_density_minimum_size
FAIL tests/unit/ui/test_theme_tokens.py::test_font_tokens_match_shell_density_scale
```

**Step 3: Implement the new shell constants and token values**

In `src/fesium/ui/shell.py`, introduce explicit constants:

```python
DEFAULT_WINDOW_GEOMETRY = "1400x960"
MIN_WINDOW_SIZE = (1100, 760)
```

Then wire them into the window setup:

```python
self.geometry(DEFAULT_WINDOW_GEOMETRY)
self.minsize(*MIN_WINDOW_SIZE)
```

In `src/fesium/ui/theme/tokens.py`, update:

```python
"heading": ("Sora", 24, "bold"),
"body": ("IBM Plex Sans", 14),
"body_medium": ("IBM Plex Sans", 14),
"mono": ("JetBrains Mono", 13),
```

**Step 4: Run the targeted tests again**

Run:

```bash
python -m pytest tests/unit/ui/test_shell.py tests/unit/ui/test_theme_tokens.py -v
```

Expected output:

```text
7 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/shell.py src/fesium/ui/theme/tokens.py tests/unit/ui/test_shell.py tests/unit/ui/test_theme_tokens.py
git commit -m "feat: increase Fesium shell baseline density"
```

## Task 2: Add Reusable Panel Surface Variants

**Files:**
- Modify: `src/fesium/ui/widgets/panel_card.py`
- Create: `tests/unit/ui/test_panel_card.py`

**Step 1: Write failing tests for panel surface resolution**

In `tests/unit/ui/test_panel_card.py`, add:

```python
from fesium.ui.widgets.panel_card import resolve_panel_surface


def test_resolve_panel_surface_supports_default_variant():
    surface = resolve_panel_surface("default")
    assert surface["outer_fg"] == "bg.panel"
    assert surface["inner_fg"] is None


def test_resolve_panel_surface_supports_inset_variants():
    inset = resolve_panel_surface("inset")
    strong = resolve_panel_surface("inset_strong")

    assert inset["inner_fg"] == "bg.panel_alt"
    assert strong["inner_fg"] == "bg.app"


def test_resolve_panel_surface_rejects_unknown_variant():
    try:
        resolve_panel_surface("unknown")
    except ValueError as exc:
        assert "Unknown panel surface variant" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown panel surface variant")
```

**Step 2: Run the new tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/ui/test_panel_card.py -v
```

Expected output:

```text
E   ImportError: cannot import name 'resolve_panel_surface'
```

**Step 3: Implement panel surface resolution and inset rendering**

In `src/fesium/ui/widgets/panel_card.py`, add a pure helper:

```python
def resolve_panel_surface(variant: str) -> dict[str, str | None]:
    variants = {
        "default": {"outer_fg": "bg.panel", "inner_fg": None},
        "inset": {"outer_fg": "bg.panel", "inner_fg": "bg.panel_alt"},
        "inset_strong": {"outer_fg": "bg.panel", "inner_fg": "bg.app"},
    }
    try:
        return variants[variant]
    except KeyError as exc:
        raise ValueError(f"Unknown panel surface variant: {variant}") from exc
```

Update `PanelCard` so it accepts:

```python
surface_variant: str = "default"
```

and, for inset variants, creates a child inner frame such as:

```python
self.inner_frame = ctk.CTkFrame(
    self,
    fg_color=get_color_token(surface["inner_fg"]),
    corner_radius=14,
    border_width=0,
)
```

Only create `inner_frame` for inset variants. The default variant should keep the current simpler surface.

**Step 4: Run the panel-card tests**

Run:

```bash
python -m pytest tests/unit/ui/test_panel_card.py -v
```

Expected output:

```text
3 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/widgets/panel_card.py tests/unit/ui/test_panel_card.py
git commit -m "feat: add inset panel surface variants"
```

## Task 3: Add a Reusable Scrollable View Body Widget

**Files:**
- Create: `src/fesium/ui/widgets/scrollable_view_body.py`
- Create: `tests/unit/ui/test_scrollable_view_body.py`

**Step 1: Write failing tests for the scroll-body style contract**

In `tests/unit/ui/test_scrollable_view_body.py`, add:

```python
from fesium.ui.widgets.scrollable_view_body import resolve_scrollable_view_body_style


def test_scrollable_view_body_uses_app_background():
    style = resolve_scrollable_view_body_style()
    assert style["fg_color"] == "transparent"
    assert style["scrollbar_fg"] == "bg.app"
    assert style["scrollbar_button"] == "bg.panel"
```

**Step 2: Run the new test to verify it fails**

Run:

```bash
python -m pytest tests/unit/ui/test_scrollable_view_body.py -v
```

Expected output:

```text
E   ModuleNotFoundError: No module named 'fesium.ui.widgets.scrollable_view_body'
```

**Step 3: Implement the reusable scroll-body widget**

In `src/fesium/ui/widgets/scrollable_view_body.py`, add:

```python
import customtkinter as ctk

from fesium.ui.theme.styles import get_color_token


def resolve_scrollable_view_body_style() -> dict[str, str]:
    return {
        "fg_color": "transparent",
        "scrollbar_fg": "bg.app",
        "scrollbar_button": "bg.panel",
        "scrollbar_button_hover": "bg.panel_alt",
    }


class ScrollableViewBody(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        style = resolve_scrollable_view_body_style()
        super().__init__(
            master,
            fg_color=style["fg_color"],
            scrollbar_fg_color=get_color_token(style["scrollbar_fg"]),
            scrollbar_button_color=get_color_token(style["scrollbar_button"]),
            scrollbar_button_hover_color=get_color_token(style["scrollbar_button_hover"]),
            **kwargs,
        )
```

Keep this widget intentionally small. It is only the shared scroll container.

**Step 4: Run the scroll-body test**

Run:

```bash
python -m pytest tests/unit/ui/test_scrollable_view_body.py -v
```

Expected output:

```text
1 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/widgets/scrollable_view_body.py tests/unit/ui/test_scrollable_view_body.py
git commit -m "feat: add reusable scrollable view body"
```

## Task 4: Make `ServerView` Scroll-Safe and Responsive

**Files:**
- Modify: `src/fesium/ui/views/server_view.py`
- Modify: `tests/unit/ui/test_server_view.py`

**Step 1: Extend the `ServerView` tests with responsive layout helpers**

In `tests/unit/ui/test_server_view.py`, add:

```python
from fesium.ui.views.server_view import build_server_view_model, resolve_server_action_layout


def test_resolve_server_action_layout_keeps_single_row_on_wide_width():
    layout = resolve_server_action_layout(available_width=1200)
    assert layout == [
        ["select_project", "start", "stop", "restart", "open_in_browser"],
    ]


def test_resolve_server_action_layout_wraps_to_two_rows_when_narrow():
    layout = resolve_server_action_layout(available_width=760)
    assert layout == [
        ["select_project", "start", "stop"],
        ["restart", "open_in_browser"],
    ]


def test_build_server_view_model_keeps_log_text():
    model = build_server_view_model(
        project_root=Path("C:/Projects/demo"),
        project_kind="standard",
        document_root=Path("C:/Projects/demo"),
        backend_kind="static",
        server_status="running",
        local_url="http://localhost:8000",
        last_error="",
        log_lines=("Line 1", "Line 2"),
    )

    assert model["log_text"] == "Line 1\\nLine 2"
```

**Step 2: Run the targeted server-view tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/ui/test_server_view.py -v
```

Expected output:

```text
E   ImportError: cannot import name 'resolve_server_action_layout'
```

**Step 3: Implement responsive layout helpers and scroll-body integration**

In `src/fesium/ui/views/server_view.py`:

- add a pure helper:

```python
def resolve_server_action_layout(available_width: int) -> list[list[str]]:
    if available_width >= 980:
        return [["select_project", "start", "stop", "restart", "open_in_browser"]]
    return [
        ["select_project", "start", "stop"],
        ["restart", "open_in_browser"],
    ]
```

- replace the direct root-grid stacking with a `ScrollableViewBody`
- keep the title row outside or at the top of that body, but ensure the content beneath it scrolls vertically
- render the control buttons from the layout helper rather than from a hard-coded five-column single row
- use `PanelCard(surface_variant="inset_strong")` for the log panel
- keep `PanelCard(surface_variant="inset")` for the details and controls panels if the composition looks balanced

Keep the action enable/disable logic exactly as it works now.

**Step 4: Run the server-view tests again**

Run:

```bash
python -m pytest tests/unit/ui/test_server_view.py -v
```

Expected output:

```text
4 passed
```

**Step 5: Commit**

```bash
git add src/fesium/ui/views/server_view.py tests/unit/ui/test_server_view.py
git commit -m "feat: make server view responsive and scroll-safe"
```

## Task 5: Apply the Shared Scroll Pattern to Secondary Views

**Files:**
- Modify: `src/fesium/ui/views/database_view.py`
- Modify: `src/fesium/ui/views/environment_view.py`
- Modify: `src/fesium/ui/views/settings_view.py`
- Run: `tests/unit/ui/test_database_view.py`
- Run: `tests/unit/ui/test_environment_view.py`
- Run: `tests/unit/ui/test_settings_view.py`

**Step 1: Use the existing summary tests as regression guards**

Run:

```bash
python -m pytest tests/unit/ui/test_database_view.py tests/unit/ui/test_environment_view.py tests/unit/ui/test_settings_view.py -v
```

Expected output:

```text
3 passed
```

These tests already lock the pure data-shaping helpers. They are sufficient for this task because the visual change is structural and the detailed widget behavior will be verified in the manual launch check.

**Step 2: Integrate the shared scroll-body widget**

In each of these files:

- `src/fesium/ui/views/database_view.py`
- `src/fesium/ui/views/environment_view.py`
- `src/fesium/ui/views/settings_view.py`

wrap the panel content inside `ScrollableViewBody` instead of placing everything directly on the root frame.

Keep the current user-facing content the same:

- `Database` still shows the selected database and read-only badge
- `Environment` still shows PHP summary and version rows
- `Settings` still shows the current config summary

Do not convert `Overview` to the shared scroll-body pattern in this milestone.

**Step 3: Re-run the regression tests**

Run:

```bash
python -m pytest tests/unit/ui/test_database_view.py tests/unit/ui/test_environment_view.py tests/unit/ui/test_settings_view.py -v
```

Expected output:

```text
3 passed
```

**Step 4: Commit**

```bash
git add src/fesium/ui/views/database_view.py src/fesium/ui/views/environment_view.py src/fesium/ui/views/settings_view.py
git commit -m "feat: add shared scroll layout to secondary views"
```

## Task 6: Update User-Facing Docs and Verify the Milestone

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Run: full test and launch verification

**Step 1: Update the public docs**

In `README.md`, update the current UI/feature summary so it reflects:

- larger default desktop shell
- improved panel readability
- scroll-safe view bodies
- responsive `Server` controls
- refined inset panel styling

In `CHANGELOG.md`, add an entry under the current unreleased section or next version bucket that summarizes the same UX-polish milestone in user-facing language.

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
the desktop app opens with the larger default shell and can be closed normally
```

During the manual check in the running app, verify:

- the `Server` view no longer clips its control row at the default size
- the log panel is visible without resizing
- shrinking the window uses vertical scrolling and control reflow instead of layout breakage
- the inset surface treatment looks refined rather than heavy-handed
- `Overview` still reads as a fast landing view rather than a scrolled utility screen

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: document shell density and layout polish"
```

## Final Checkpoint

At the end of the milestone:

- `git status --short` should not include `docs/assets/screenshots/fesium-overview.png` unless the user explicitly wants it committed
- all unit tests should pass
- the app should be manually checked at the new default shell size
- the milestone should remain strictly visual and structural, without changing server-flow behavior
