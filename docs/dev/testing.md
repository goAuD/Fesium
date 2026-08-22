# Testing

Fesium uses `pytest`. The suite is pure-Python and runs without a display, without PHP, and without network access.

## Run the Full Suite

```bash
python -m pytest -v
```

## Run Only Unit Tests

```bash
python -m pytest tests/unit -v
```

## Layout

```text
tests/
└── unit/
    ├── app/     Mirrors src/fesium/app/
    ├── core/    Mirrors src/fesium/core/
    └── ui/      Mirrors src/fesium/ui/
```

When you change source code under `src/fesium/`, add or update the matching test under `tests/unit/` in the same-named subfolder.

## Testing Guidelines

- Prefer testing pure view-model functions (e.g. `build_server_view_model`, `build_database_summary`) over rendered widgets.
- Use `tmp_path` for any filesystem interaction; never touch `~/.fesium` from a test.
- Use `monkeypatch` to stub subprocess calls (`php -v`, server startup).
- Do not introduce tests that require a running PHP or network access.
- A test that needs a display is allowed only when it skips cleanly without one, and only when it is not the sole coverage for the behaviour. Ubuntu CI has no X server; Windows and macOS runners do. Share a single session-scoped Tk root - destroying one leaves the interpreter unable to create another, so per-test roots skip everything after the first for a reason unrelated to the display.
- A layout assertion should carry a control case that reproduces the defect in the same run. `tests/unit/ui/test_width_agnostic_label.py` asserts that a plain label collapses and the widget under test does not, so the test cannot quietly stop measuring anything.

## Layout checks

The suite is display-free, so it cannot see a layout bug. `scripts/check_layout.py` can: it drives the real views in a live window and asserts on measurements.

```bash
python scripts/check_layout.py
```

It measures three things, each of which has been a real defect here: every label has room for its text, no layout keeps resizing once the window stops, and tiles of equal span come out equal width. Run it before calling a UI change done, and prove any new assertion by reintroducing the defect and watching it fail - a check that has never failed has not been tested.

## CI

Tests run on every push and pull request via [.github/workflows/python-tests.yml](../../.github/workflows/python-tests.yml).
